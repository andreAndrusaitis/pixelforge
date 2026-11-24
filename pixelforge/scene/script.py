"""Roteiro de cena: leitura e validação.

O roteiro é um JSON com chaves em português (ver docs/manual.md, seção Cenas). Este
módulo só valida e normaliza; quem carrega artes é `library`, quem calcula o
tempo é `timeline`. Erros apontam o plano e o campo (`plano 2, camera.de: ...`).
Campos que começam com `_` são comentários e são ignorados.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..palettes import parse_color

RGB = tuple[int, int, int]

SCENE_KEYS = ("name", "resolucao", "escala", "fps", "cenario", "fundo", "atores", "planos",
              "transicoes", "efeitos", "audio")
SHOT_KEYS = ("dur", "camera", "cenario", "fundo", "transicao", "acoes", "dialogo", "efeitos",
             "titulo", "legenda", "sons", "ia")
CAMERA_KEYS = ("pos", "de", "para", "curva", "seguir", "folga", "enquadrar", "em", "zoom", "tremor")
ACTOR_KEYS = ("sprite", "pos", "olhar", "anim", "visivel", "nome", "voz", "tom")
ACTION_KEYS = ("ator", "inicio", "pos", "ate", "vel", "dur", "anim", "depois", "olhar",
               "aparecer", "sumir", "fade", "som")
DIALOG_KEYS = ("ator", "nome", "retrato", "texto", "velocidade", "pausa", "inicio", "fim", "posicao",
               "voz", "arquivo", "close")
TITLE_KEYS = ("texto", "subtitulo", "inicio", "dur", "fade", "fundo", "cor", "posicao")
CAPTION_KEYS = ("texto", "inicio", "dur", "posicao", "narrar", "voz", "cor")
AUDIO_KEYS = ("trilha", "ambiente", "eventos", "falas", "abafar", "volume")
VOICE_KEYS = ("modo", "voz", "narrador", "velocidade", "volume", "bip")
SOUND_SOURCES = ("arquivo", "efeito", "musica", "texto", "descricao")
SOUND_KEYS = (*SOUND_SOURCES, "inicio", "t", "plano", "volume", "fade_in", "fade_out", "pan", "loop",
              "semente", "variar", "voz", "velocidade", "duracao", "repetir")
VOICE_MODES = ("auto", "bip", "nenhum")
AI_KEYS = ("origem", "movimento", "dur", "inicio", "imagem", "ator", "regiao", "semente", "fps", "laco", "paleta")
AI_ORIGINS = ("quadro", "imagem", "sprite")
AI_LOOPS = ("vaivem", "repetir", "segurar")
AI_MAX_DUR = 5.0   # s de clipe por geração (o resto é laço)
FRAMINGS = {"geral": 1, "medio": 2, "close": 3}    # enquadramento → zoom padrão
CLOSEUPS = ("retrato", "ator")
TRANSITION_KEYS = ("tipo", "dur", "degraus", "cor")
TRANSITIONS = ("corte", "fade", "fade-branco", "cortina")
CURVES = ("linear", "suave")
FACING = ("direita", "esquerda")
FADE_DUR = 1.0     # s: entrada/saída inteiras; entre planos, metade em cada lado
FADE_STEPS = 4     # degraus do fade (visual retrô)
WALK_SPEED = 40.0  # px/s
TYPE_SPEED = 30.0  # letras/s
DIALOG_HOLD = 1.5  # s de leitura depois da última página
TITLE_DUR = 3.5    # s de um plano só com título, sem `dur`
TITLE_FADE = 0.5   # s do texto do título aparecendo/sumindo
CAPTION_RATE = 15  # letras/s de leitura de uma legenda sem `dur`
CAPTION_MIN = 1.5  # s mínimos de uma legenda sem `dur`
DUCK = 0.4         # trilha/ambiente durante as falas (0–1)

# Efeitos: tipo → {campo: valor padrão}. `inicio`/`dur` (s, relativos ao plano) valem para todos.
EFFECTS: dict[str, dict] = {
    "chuva": {"intensidade": 0.5, "vento": 1, "cor": "#8b9bb4"},
    "neblina": {"intensidade": 0.4, "cor": "#c0cbdc", "velocidade": 6},
    "particulas": {"estilo": "poeira", "quantidade": 30, "cor": None},
    "tinta": {"modo": "noite", "cor": None, "intensidade": 1.0},
    "luz": {"pos": None, "raio": 24, "cor": "#feae34", "intensidade": 0.5, "piscar": 0.3},
    "flash": {"cor": "#ffffff"},
    "vinheta": {"intensidade": 0.5, "cor": "#000000"},
}
PARTICLE_STYLES = ("folhas", "brasas", "poeira", "neve", "vagalumes")
TINT_MODES = ("noite", "dia", "sepia", "por-do-sol")

# Campos do design que ainda não existem: erro com explicação, não silêncio.
FUTURE = {
    "paleta": "paleta da cena (ainda não suportada)",
}


class SceneError(ValueError):
    pass


@dataclass
class Transition:
    kind: str = "corte"
    dur: float = FADE_DUR
    steps: int = FADE_STEPS
    custom_color: RGB | None = None

    @property
    def color(self) -> RGB:
        if self.custom_color is not None:
            return self.custom_color
        return (255, 255, 255) if self.kind == "fade-branco" else (0, 0, 0)


@dataclass
class CameraSpec:
    """`pos` fixo, movimento `de` → `para`, ou `seguir` um ator. `de` ausente = onde a câmera está."""

    pos: tuple[int, int] | None = None
    start: tuple[int, int] | None = None
    end: tuple[int, int] | None = None
    curve: str = "linear"
    follow: str | None = None
    slack: int = 0                           # folga do `seguir`: px que o ator anda sem a câmera mexer
    framing: str | None = None               # geral | medio | close
    target: str | None = None                # ator do enquadramento
    zoom: int | None = None
    shake: tuple[int, float] | None = None   # (amplitude px, duração s)


@dataclass
class ActorSpec:
    name: str
    sprite: str
    pos: tuple[int, int]
    facing: str = "direita"
    anim: str | None = None
    visible: bool = True
    label: str | None = None                 # nome mostrado no diálogo
    voice: str | None = None                 # voz por IA das falas
    pitch: float | None = None               # Hz do bipe de máquina de escrever


@dataclass
class Action:
    actor: str
    where: str                                # "plano 2, acao 1" (para mensagens)
    start: float = 0.0
    pos: tuple[int, int] | None = None
    to: tuple[int, int] | None = None
    speed: float = WALK_SPEED
    dur: float | None = None
    anim: str | None = None
    after: str | None = None
    facing: str | None = None
    appear: bool = False
    vanish: bool = False
    fade: float = 0.0
    sound: "Sound | None" = None


@dataclass
class Sound:
    """Um som do roteiro. `source` vai para `pixelforge.audio.mix.load_source`
    (`arquivo`, `efeito`, `musica`, `texto`) ou para a IA de ambiente/trilha (`descricao`)."""

    source: dict
    where: str
    start: float = 0.0                        # s: absoluto no `audio`, relativo ao plano/ação nos demais
    shot: int | None = None                   # `plano`: `start` passa a contar do início desse plano
    volume: float = 1.0
    fade_in: float | None = None
    fade_out: float | None = None
    pan: float = 0.0
    loop: bool = False
    repeat: float | None = None               # s entre repetições enquanto o ator anda

    @property
    def kind(self) -> str:
        return next(k for k in SOUND_SOURCES if k in self.source)


@dataclass
class AISpec:
    """Animação por IA (pixelforge.ai_video): imagem → vídeo → pixel art com a paleta travada."""

    origin: str                               # quadro | imagem | sprite | camada
    motion: str                               # descrição do movimento
    where: str
    dur: float | None = None                  # s de clipe (None = o plano, até AI_MAX_DUR)
    start: float = 0.0                        # s, relativo ao plano
    image: str | None = None                  # origem imagem
    actor: str | None = None                  # origem sprite
    regions: list[tuple[int, int, int, int]] = field(default_factory=list)   # [x, y, l, a]: só isto muda
    seed: int = 0
    fps: int | None = None                    # None = fps da cena
    loop: str = "segurar"                     # depois do fim do clipe: vaivem | repetir | segurar
    palette_from: list[str] = field(default_factory=list)   # artes cujas cores entram na paleta travada


@dataclass
class VoiceSpec:
    mode: str = "auto"                        # auto: IA se houver, senão bipes
    voice: str | None = None
    narrator: str | None = None
    speed: float = 1.0
    volume: float = 1.0
    bip: float = 0.35                         # volume dos bipes de máquina de escrever


@dataclass
class AudioSpec:
    track: Sound | None = None
    ambience: list[Sound] = field(default_factory=list)
    events: list[Sound] = field(default_factory=list)
    voices: VoiceSpec = field(default_factory=VoiceSpec)
    duck: float = DUCK
    volume: float = 1.0


@dataclass
class Title:
    text: str
    where: str
    subtitle: str | None = None
    start: float = 0.0
    dur: float | None = None                  # None = até o fim do plano
    fade: float = TITLE_FADE
    background: RGB | None = (0, 0, 0)        # None = sobre a cena
    color: RGB = (255, 255, 255)
    position: str = "centro"


@dataclass
class Caption:
    """Legenda/narração em texto sobre o vídeo."""

    text: str
    where: str
    start: float | None = None                # None = logo depois da anterior
    dur: float | None = None                  # None = pelo tamanho do texto
    position: str = "baixo"
    narrate: bool = False                     # lida pela voz do narrador (bloco `audio`)
    voice: str | None = None
    color: RGB = (255, 255, 255)

    @property
    def length(self) -> float:
        return self.dur if self.dur is not None else max(CAPTION_MIN, len(self.text) / CAPTION_RATE + 1.0)


@dataclass
class Line:
    """Uma fala (caixa de diálogo)."""

    text: str
    where: str
    actor: str | None = None
    label: str | None = None
    portrait: str | None = None
    speed: float = TYPE_SPEED
    pause: float = 1.0
    start: float | None = None                # None = logo depois da fala anterior
    hold: float = DIALOG_HOLD
    position: str = "baixo"
    voice: str | None = None
    audio: str | None = None                  # WAV gravado da fala
    closeup: str | None = None                # retrato | ator: corte para close enquanto fala


@dataclass
class Effect:
    kind: str
    params: dict
    where: str
    start: float = 0.0
    dur: float | None = None


@dataclass
class Shot:
    index: int                       # 1, 2, 3... (como aparece nas mensagens)
    dur: float | None                # None = calculada pelo diálogo
    camera: CameraSpec | None = None
    backdrop: str | dict | None = None
    background: RGB | None = None
    transition: Transition | None = None
    actions: list[Action] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    title: Title | None = None
    captions: list[Caption] = field(default_factory=list)
    sounds: list[Sound] = field(default_factory=list)
    ai: AISpec | None = None


@dataclass
class Scene:
    name: str
    path: Path | None
    shots: list[Shot]
    backdrop: str | dict | None = None
    background: RGB = (0, 0, 0)
    resolution: str | list | None = None   # bruto; resolvido com os presets da config
    scale: int | None = None
    fps: int | None = None
    intro: Transition = field(default_factory=Transition)
    outro: Transition = field(default_factory=Transition)
    actors: dict[str, ActorSpec] = field(default_factory=dict)
    effects: list[Effect] = field(default_factory=list)
    audio: AudioSpec | None = None

    @property
    def folder(self) -> Path | None:
        return self.path.parent if self.path else None

    @property
    def duration(self) -> float:
        """Soma das durações explícitas (planos de diálogo sem `dur` contam 0)."""
        return sum(s.dur or 0 for s in self.shots)


# --------------------------------------------------------------------------


def load_scene(path: str | Path) -> Scene:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"roteiro não encontrado: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SceneError(f"{path}: JSON inválido ({exc})") from None
    try:
        return parse_scene(data, path)
    except SceneError as exc:
        raise SceneError(f"{path.name}: {exc}") from None


def parse_scene(data: dict, path: Path | None = None) -> Scene:
    if not isinstance(data, dict):
        raise SceneError("o roteiro deve ser um objeto JSON")
    check_keys(data, SCENE_KEYS, "roteiro")

    actors = parse_actors(data.get("atores", {}))
    shots_raw = data.get("planos")
    if not isinstance(shots_raw, list) or not shots_raw:
        raise SceneError("'planos' é obrigatório: lista com ao menos um plano")
    shots = [parse_shot(raw, i + 1, actors) for i, raw in enumerate(shots_raw)]
    if "cenario" not in data and shots[0].backdrop is None:
        raise SceneError("informe 'cenario' no roteiro ou no plano 1")

    scene = Scene(
        name=_name(data.get("name"), path),
        path=path,
        shots=shots,
        backdrop=_backdrop_ref(data.get("cenario"), "cenario"),
        background=_color(data.get("fundo", "#000000"), "fundo"),
        resolution=data.get("resolucao"),
        scale=_positive_int(data["escala"], "escala") if "escala" in data else None,
        fps=_positive_int(data["fps"], "fps", maximum=60) if "fps" in data else None,
        actors=actors,
        effects=parse_effects(data.get("efeitos", []), "efeitos"),
        audio=parse_audio(data["audio"], len(shots)) if data.get("audio") is not None else None,
    )
    if scene.resolution is not None:
        parse_resolution(scene.resolution, None)  # valida o formato já aqui
    transitions = data.get("transicoes", {})
    if not isinstance(transitions, dict):
        raise SceneError("transicoes: esperado objeto com 'entrada' e/ou 'saida'")
    check_keys(transitions, ("entrada", "saida"), "transicoes")
    scene.intro = parse_transition(transitions.get("entrada", "corte"), "transicoes.entrada")
    scene.outro = parse_transition(transitions.get("saida", "corte"), "transicoes.saida")
    return scene


def parse_actors(raw) -> dict[str, ActorSpec]:
    if not isinstance(raw, dict):
        raise SceneError("atores: esperado objeto {nome: {sprite, pos, ...}}")
    actors = {}
    for name, spec in raw.items():
        where = f"atores.{name}"
        if not isinstance(spec, dict):
            raise SceneError(f"{where}: esperado objeto com 'sprite' e 'pos'")
        check_keys(spec, ACTOR_KEYS, where)
        for required in ("sprite", "pos"):
            if required not in spec:
                raise SceneError(f"{where}.{required}: obrigatório")
        if not isinstance(spec["sprite"], str) or not spec["sprite"].strip():
            raise SceneError(f"{where}.sprite: caminho da arte (ex.: \"personagens/ana\")")
        visible = spec.get("visivel", True)
        if not isinstance(visible, bool):
            raise SceneError(f"{where}.visivel: esperado true ou false")
        actors[name] = ActorSpec(
            name, spec["sprite"], _point(spec["pos"], f"{where}.pos"),
            _choice(spec.get("olhar", "direita"), FACING, f"{where}.olhar"),
            _text(spec["anim"], f"{where}.anim") if "anim" in spec else None,
            visible,
            _label(spec.get("nome"), f"{where}.nome"),
            _text(spec["voz"], f"{where}.voz") if "voz" in spec else None,
            _positive_float(spec["tom"], f"{where}.tom") if "tom" in spec else None,
        )
    return actors


def parse_shot(raw, index: int, actors: dict[str, ActorSpec] | None = None) -> Shot:
    where = f"plano {index}"
    actors = actors or {}
    if not isinstance(raw, dict):
        raise SceneError(f"{where}: esperado objeto")
    try:
        check_keys(raw, SHOT_KEYS, "plano")
        if "dur" not in raw and "dialogo" not in raw and "titulo" not in raw:
            raise SceneError("dur: obrigatório (duração em segundos; só planos com diálogo ou título podem omitir)")
        shot = Shot(index, _positive_float(raw["dur"], "dur") if "dur" in raw else None)
        if "camera" in raw:
            shot.camera = parse_camera(raw["camera"], actors)
        if "cenario" in raw:
            shot.backdrop = _backdrop_ref(raw["cenario"], "cenario")
        if "fundo" in raw:
            shot.background = _color(raw["fundo"], "fundo")
        if "transicao" in raw:
            if index == 1:
                raise SceneError("transicao: o plano 1 não tem plano anterior; use transicoes.entrada")
            shot.transition = parse_transition(raw["transicao"], "transicao")
        if "acoes" in raw:
            if not isinstance(raw["acoes"], list):
                raise SceneError("acoes: esperado lista de ações")
            shot.actions = [parse_action(a, f"acao {i + 1}", actors, where)
                            for i, a in enumerate(raw["acoes"])]
        if "dialogo" in raw:
            lines = raw["dialogo"] if isinstance(raw["dialogo"], list) else [raw["dialogo"]]
            if not lines:
                raise SceneError("dialogo: lista vazia")
            shot.lines = [parse_line(l, "dialogo" if len(lines) == 1 else f"dialogo {i + 1}", actors, where)
                          for i, l in enumerate(lines)]
        shot.effects = parse_effects(raw.get("efeitos", []), "efeitos", where)
        if "titulo" in raw:
            shot.title = parse_title(raw["titulo"], "titulo")
            if shot.dur is None and not shot.lines:
                shot.dur = shot.title.start + shot.title.dur if shot.title.dur is not None else TITLE_DUR
        if "legenda" in raw:
            items = raw["legenda"] if isinstance(raw["legenda"], list) else [raw["legenda"]]
            if not items:
                raise SceneError("legenda: lista vazia")
            shot.captions = [parse_caption(c, "legenda" if len(items) == 1 else f"legenda {i + 1}", where)
                             for i, c in enumerate(items)]
        if "ia" in raw:
            shot.ai = parse_ai(raw["ia"], "ia", actors, where)
        if "sons" in raw:
            if not isinstance(raw["sons"], list):
                raise SceneError("sons: esperado lista, ex.: [{\"efeito\": \"porta\", \"inicio\": 1}]")
            shot.sounds = [parse_sound(s, f"sons[{i + 1}]", where) for i, s in enumerate(raw["sons"])]
    except SceneError as exc:
        message = str(exc)
        raise SceneError(f"{where}: {message}" if message.startswith("campo") else f"{where}, {message}") from None
    return shot


def parse_camera(raw, actors: dict[str, ActorSpec] | None = None) -> CameraSpec:
    if not isinstance(raw, dict):
        raise SceneError("camera: esperado objeto, ex.: {\"de\": [0, 0], \"para\": [120, 0]}")
    check_keys(raw, CAMERA_KEYS, "camera")
    if "pos" in raw and ("de" in raw or "para" in raw):
        raise SceneError("camera: use 'pos' (parada) ou 'de'/'para' (movimento), não os dois")
    if "seguir" in raw and ("de" in raw or "para" in raw):
        raise SceneError("camera: 'seguir' não combina com 'de'/'para'")
    if "de" in raw and "para" not in raw:
        raise SceneError("camera: 'de' precisa de 'para'")
    if "curva" in raw and "para" not in raw:
        raise SceneError("camera.curva: só vale com 'para'")
    follow = raw.get("seguir")
    if follow is not None and follow not in (actors or {}):
        raise SceneError(f"camera.seguir: ator '{follow}' não existe em 'atores'")
    if "folga" in raw and follow is None:
        raise SceneError("camera.folga: só vale com 'seguir'")
    slack = raw.get("folga", 0)
    if isinstance(slack, bool) or not isinstance(slack, int) or slack < 0:
        raise SceneError(f"camera.folga: esperado inteiro >= 0 (px), não {slack!r}")
    framing, target = raw.get("enquadrar"), raw.get("em")
    if framing is not None:
        framing = _choice(framing, tuple(FRAMINGS), "camera.enquadrar")
        if any(k in raw for k in ("pos", "de", "para")):
            raise SceneError("camera.enquadrar: não combina com 'pos'/'de'/'para' (o enquadramento calcula a posição)")
        if target is None and follow is not None:
            target = follow
        if target is None and framing != "geral":
            raise SceneError(f"camera.enquadrar \"{framing}\": diga em quem com 'em': \"<ator>\"")
    elif target is not None:
        raise SceneError("camera.em: só vale com 'enquadrar'")
    if target is not None and target not in (actors or {}):
        raise SceneError(f"camera.em: ator '{target}' não existe em 'atores'")
    zoom = raw.get("zoom")
    if zoom is not None:
        zoom = _positive_int(zoom, "camera.zoom", maximum=4)
    shake = raw.get("tremor")
    if shake is not None:
        if (not isinstance(shake, (list, tuple)) or len(shake) != 2 or isinstance(shake[0], bool)
                or not isinstance(shake[0], int) or shake[0] < 1):
            raise SceneError(f"camera.tremor: esperado [amplitude px (inteiro), duração s], não {shake!r}")
        shake = (shake[0], _positive_float(shake[1], "camera.tremor[1]"))
    return CameraSpec(
        pos=_point(raw["pos"], "camera.pos") if "pos" in raw else None,
        start=_point(raw["de"], "camera.de") if "de" in raw else None,
        end=_point(raw["para"], "camera.para") if "para" in raw else None,
        curve=_choice(raw.get("curva", "linear"), CURVES, "camera.curva"),
        follow=follow,
        slack=slack,
        framing=framing,
        target=target,
        zoom=zoom,
        shake=shake,
    )


def parse_action(raw, label: str, actors: dict[str, ActorSpec], shot_where: str = "") -> Action:
    if not isinstance(raw, dict):
        raise SceneError(f"{label}: esperado objeto com 'ator'")
    check_keys(raw, ACTION_KEYS, label)
    actor = raw.get("ator")
    if actor not in actors:
        known = ", ".join(actors) or "nenhum declarado em 'atores'"
        raise SceneError(f"{label}.ator: '{actor}' não existe (atores: {known})")
    if raw.get("aparecer") and raw.get("sumir"):
        raise SceneError(f"{label}: use 'aparecer' ou 'sumir', não os dois")
    if not any(k in raw for k in ("pos", "ate", "anim", "olhar", "aparecer", "sumir")):
        raise SceneError(f"{label}: diga o que o ator faz: 'ate', 'pos', 'anim', 'olhar', 'aparecer' ou 'sumir'")
    for key in ("aparecer", "sumir"):
        if key in raw and not isinstance(raw[key], bool):
            raise SceneError(f"{label}.{key}: esperado true ou false")
    if isinstance(raw.get("som"), dict) and "repetir" in raw["som"] and "ate" not in raw:
        raise SceneError(f"{label}.som.repetir: só vale com 'ate' (repete enquanto o ator anda)")
    if ("vel" in raw or "dur" in raw or "depois" in raw) and "ate" not in raw:
        raise SceneError(f"{label}: 'vel', 'dur' e 'depois' só valem com 'ate'")
    return Action(
        actor=actor,
        where=f"{shot_where}, {label}" if shot_where else label,
        start=_non_negative(raw.get("inicio", 0), f"{label}.inicio"),
        pos=_point(raw["pos"], f"{label}.pos") if "pos" in raw else None,
        to=_point(raw["ate"], f"{label}.ate") if "ate" in raw else None,
        speed=_positive_float(raw["vel"], f"{label}.vel") if "vel" in raw else WALK_SPEED,
        dur=_positive_float(raw["dur"], f"{label}.dur") if "dur" in raw else None,
        anim=_text(raw["anim"], f"{label}.anim") if "anim" in raw else None,
        after=_text(raw["depois"], f"{label}.depois") if "depois" in raw else None,
        facing=_choice(raw["olhar"], FACING, f"{label}.olhar") if "olhar" in raw else None,
        appear=raw.get("aparecer", False),
        vanish=raw.get("sumir", False),
        fade=_non_negative(raw.get("fade", 0), f"{label}.fade"),
        sound=parse_sound(raw["som"], f"{label}.som", shot_where) if "som" in raw else None,
    )


def parse_line(raw, label: str, actors: dict[str, ActorSpec], shot_where: str = "") -> Line:
    if isinstance(raw, str):
        raw = {"texto": raw}
    if not isinstance(raw, dict):
        raise SceneError(f"{label}: esperado objeto com 'texto'")
    check_keys(raw, DIALOG_KEYS, label)
    text = raw.get("texto")
    if not isinstance(text, str) or not text.strip():
        raise SceneError(f"{label}.texto: obrigatório (a fala)")
    actor = raw.get("ator")
    if actor is not None and actor not in actors:
        raise SceneError(f"{label}.ator: '{actor}' não existe em 'atores'")
    if "nome" in raw:
        name = _label(raw["nome"], f"{label}.nome")
    elif actor is not None:
        name = actors[actor].label if actors[actor].label is not None else actor.capitalize()
    else:
        name = None
    portrait = raw.get("retrato")
    if portrait is not None and (not isinstance(portrait, str) or not portrait.strip()):
        raise SceneError(f"{label}.retrato: caminho da arte do retrato")
    closeup = _choice(raw["close"], CLOSEUPS, f"{label}.close") if "close" in raw else None
    if closeup == "retrato" and portrait is None:
        raise SceneError(f"{label}.close: \"retrato\" precisa de 'retrato' na fala")
    if closeup == "ator" and actor is None:
        raise SceneError(f"{label}.close: \"ator\" precisa de 'ator' na fala")
    return Line(
        text=" ".join(text.split()) if "\n" not in text else text,
        where=f"{shot_where}, {label}" if shot_where else label,
        actor=actor,
        label=name or None,
        portrait=portrait,
        speed=_positive_float(raw["velocidade"], f"{label}.velocidade") if "velocidade" in raw else TYPE_SPEED,
        pause=_non_negative(raw.get("pausa", 1.0), f"{label}.pausa"),
        start=_non_negative(raw["inicio"], f"{label}.inicio") if "inicio" in raw else None,
        hold=_non_negative(raw.get("fim", DIALOG_HOLD), f"{label}.fim"),
        position=_choice(raw.get("posicao", "baixo"), ("baixo", "cima"), f"{label}.posicao"),
        voice=_text(raw["voz"], f"{label}.voz") if "voz" in raw else None,
        audio=_text(raw["arquivo"], f"{label}.arquivo") if "arquivo" in raw else None,
        closeup=closeup,
    )


def parse_ai(raw, label: str, actors: dict[str, ActorSpec] | None = None, shot_where: str = "",
             layer: bool = False) -> AISpec:
    """`"ia"` de um plano (origem quadro/imagem/sprite) ou de uma camada do cenário (`layer`)."""
    if isinstance(raw, str):
        raw = {"movimento": raw}
    if not isinstance(raw, dict):
        raise SceneError(f"{label}: esperado objeto, ex.: {{\"origem\": \"quadro\", \"movimento\": \"vento no capim\"}}")
    check_keys(raw, AI_KEYS if not layer else tuple(k for k in AI_KEYS if k not in ("origem", "imagem", "ator")),
               label)
    motion = _text(raw.get("movimento"), f"{label}.movimento")
    origin = "camada" if layer else _choice(raw.get("origem", "quadro"), AI_ORIGINS, f"{label}.origem")
    image = actor = None
    if origin == "imagem":
        image = _text(raw.get("imagem"), f"{label}.imagem")
    elif "imagem" in raw:
        raise SceneError(f"{label}.imagem: só vale com \"origem\": \"imagem\"")
    if origin == "sprite":
        actor = raw.get("ator")
        if actor not in (actors or {}):
            raise SceneError(f"{label}.ator: com origem sprite, diga qual ator ('{actor}' não existe)")
    elif "ator" in raw:
        raise SceneError(f"{label}.ator: só vale com \"origem\": \"sprite\"")
    regions = raw.get("regiao", [])
    if isinstance(regions, list) and regions and isinstance(regions[0], int):
        regions = [regions]
    if not isinstance(regions, list):
        raise SceneError(f"{label}.regiao: [x, y, largura, altura] ou lista deles")
    rects = []
    for i, r in enumerate(regions):
        if (not isinstance(r, list) or len(r) != 4 or not all(isinstance(v, int) and not isinstance(v, bool) for v in r)
                or r[2] < 1 or r[3] < 1):
            raise SceneError(f"{label}.regiao[{i + 1}]: esperado [x, y, largura, altura] inteiros, não {r!r}")
        rects.append(tuple(r))
    if rects and origin == "sprite":
        raise SceneError(f"{label}.regiao: não vale com origem sprite (o sprite inteiro anima)")
    seed = raw.get("semente", 0)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SceneError(f"{label}.semente: esperado inteiro")
    extra = raw.get("paleta", [])
    extra = [extra] if isinstance(extra, str) else extra
    if not isinstance(extra, list) or not all(isinstance(e, str) and e.strip() for e in extra):
        raise SceneError(f"{label}.paleta: arte ou lista de artes cujas cores também valem (ex.: o sprite sem chapéu)")
    return AISpec(
        origin=origin, motion=motion, where=f"{shot_where}, {label}" if shot_where else label,
        dur=_positive_float(raw["dur"], f"{label}.dur") if "dur" in raw else None,
        start=_non_negative(raw.get("inicio", 0), f"{label}.inicio"),
        image=image, actor=actor, regions=rects, seed=seed,
        fps=_positive_int(raw["fps"], f"{label}.fps", maximum=24) if "fps" in raw else None,
        loop=_choice(raw.get("laco", "vaivem" if layer else "segurar"), AI_LOOPS, f"{label}.laco"),
        palette_from=extra,
    )


def parse_title(raw, where: str) -> Title:
    if isinstance(raw, str):
        raw = {"texto": raw}
    if not isinstance(raw, dict):
        raise SceneError(f"{where}: esperado texto ou objeto com 'texto'")
    check_keys(raw, TITLE_KEYS, where)
    text = raw.get("texto")
    if not isinstance(text, str) or not text.strip():
        raise SceneError(f"{where}.texto: obrigatório (ex.: \"Capítulo 7\")")
    subtitle = raw.get("subtitulo")
    if subtitle is not None and (not isinstance(subtitle, str) or not subtitle.strip()):
        raise SceneError(f"{where}.subtitulo: esperado texto")
    background = raw.get("fundo", "#000000")
    return Title(
        text=text.strip(),
        where=where,
        subtitle=subtitle.strip() if subtitle else None,
        start=_non_negative(raw.get("inicio", 0), f"{where}.inicio"),
        dur=_positive_float(raw["dur"], f"{where}.dur") if "dur" in raw else None,
        fade=_non_negative(raw.get("fade", TITLE_FADE), f"{where}.fade"),
        background=None if background is None else _color(background, f"{where}.fundo"),
        color=_color(raw.get("cor", "#ffffff"), f"{where}.cor"),
        position=_choice(raw.get("posicao", "centro"), ("centro", "baixo"), f"{where}.posicao"),
    )


def parse_caption(raw, label: str, shot_where: str = "") -> Caption:
    if isinstance(raw, str):
        raw = {"texto": raw}
    if not isinstance(raw, dict):
        raise SceneError(f"{label}: esperado texto ou objeto com 'texto'")
    check_keys(raw, CAPTION_KEYS, label)
    text = raw.get("texto")
    if not isinstance(text, str) or not text.strip():
        raise SceneError(f"{label}.texto: obrigatório")
    narrate = raw.get("narrar", False)
    if not isinstance(narrate, bool):
        raise SceneError(f"{label}.narrar: esperado true ou false")
    return Caption(
        text=" ".join(text.split()) if "\n" not in text else text,
        where=f"{shot_where}, {label}" if shot_where else label,
        start=_non_negative(raw["inicio"], f"{label}.inicio") if "inicio" in raw else None,
        dur=_positive_float(raw["dur"], f"{label}.dur") if "dur" in raw else None,
        position=_choice(raw.get("posicao", "baixo"), ("baixo", "cima"), f"{label}.posicao"),
        narrate=narrate,
        voice=_text(raw["voz"], f"{label}.voz") if "voz" in raw else None,
        color=_color(raw.get("cor", "#ffffff"), f"{label}.cor"),
    )


def parse_sound(raw, label: str, shot_where: str = "", shots: int | None = None) -> Sound:
    """Um som: nome de preset (`"porta"`) ou objeto com uma fonte e ajustes."""
    where = f"{shot_where}, {label}" if shot_where else label
    if isinstance(raw, str):
        raw = {"efeito": raw}
    if not isinstance(raw, dict):
        raise SceneError(f"{label}: esperado nome de efeito (\"passo\") ou objeto com uma fonte "
                         f"({', '.join(SOUND_SOURCES)})")
    check_keys(raw, SOUND_KEYS, label)
    sources = [k for k in SOUND_SOURCES if k in raw]
    if len(sources) != 1:
        raise SceneError(f"{label}: informe exatamente uma fonte: {', '.join(SOUND_SOURCES)}")
    kind = sources[0]
    value = raw[kind]
    if kind in ("efeito", "musica"):
        if not (isinstance(value, dict) or (isinstance(value, str) and value.strip())):
            what = "preset (passo, porta…), arquivo .json ou objeto com camadas" if kind == "efeito" \
                else "arquivo .json do sequenciador ou objeto com canais"
            raise SceneError(f"{label}.{kind}: {what}")
    else:
        _text(value, f"{label}.{kind}")
    if "t" in raw and "inicio" in raw:
        raise SceneError(f"{label}: use 'inicio' ou 't', não os dois")
    if "plano" in raw:
        if shots is None:
            raise SceneError(f"{label}.plano: só vale em audio.eventos (aqui o tempo já é relativo)")
        _positive_int(raw["plano"], f"{label}.plano", maximum=shots)
    if "semente" in raw and (isinstance(raw["semente"], bool) or not isinstance(raw["semente"], int)):
        raise SceneError(f"{label}.semente: esperado inteiro")
    for key in ("variar", "velocidade", "duracao"):
        if key in raw:
            _non_negative(raw[key], f"{label}.{key}")
    pan = raw.get("pan", 0.0)
    if isinstance(pan, bool) or not isinstance(pan, (int, float)) or not -1 <= pan <= 1:
        raise SceneError(f"{label}.pan: esperado número entre -1 e 1, não {pan!r}")
    loop = raw.get("loop", False)
    if not isinstance(loop, bool):
        raise SceneError(f"{label}.loop: esperado true ou false")
    return Sound(
        source={k: raw[k] for k in (kind, "voz", "velocidade", "semente", "variar", "duracao") if k in raw},
        where=where,
        start=_non_negative(raw.get("inicio", raw.get("t", 0)), f"{label}.inicio"),
        shot=raw.get("plano"),
        volume=_non_negative(raw.get("volume", 1.0), f"{label}.volume"),
        fade_in=_non_negative(raw["fade_in"], f"{label}.fade_in") if "fade_in" in raw else None,
        fade_out=_non_negative(raw["fade_out"], f"{label}.fade_out") if "fade_out" in raw else None,
        pan=float(pan),
        loop=loop,
        repeat=_positive_float(raw["repetir"], f"{label}.repetir") if "repetir" in raw else None,
    )


def parse_audio(raw, shots: int) -> AudioSpec:
    where = "audio"
    if not isinstance(raw, dict):
        raise SceneError(f"{where}: esperado objeto com trilha, ambiente, eventos e/ou falas")
    check_keys(raw, AUDIO_KEYS, where)
    spec = AudioSpec()
    if raw.get("trilha") is not None:
        spec.track = parse_sound(raw["trilha"], f"{where}.trilha")
        spec.track.loop = raw["trilha"].get("loop", True) if isinstance(raw["trilha"], dict) else True
    ambience = raw.get("ambiente", [])
    items = ambience if isinstance(ambience, list) else [ambience]
    for i, item in enumerate(items):
        sound = parse_sound(item, f"{where}.ambiente" if items is not ambience else f"{where}.ambiente[{i + 1}]")
        sound.loop = item.get("loop", True) if isinstance(item, dict) else True
        spec.ambience.append(sound)
    events = raw.get("eventos", [])
    if not isinstance(events, list):
        raise SceneError(f"{where}.eventos: esperado lista, ex.: [{{\"inicio\": 3, \"efeito\": \"porta\"}}]")
    spec.events = [parse_sound(e, f"{where}.eventos[{i + 1}]", shots=shots) for i, e in enumerate(events)]
    voices = raw.get("falas", {})
    if isinstance(voices, str):
        voices = {"modo": voices}
    if not isinstance(voices, dict):
        raise SceneError(f"{where}.falas: esperado objeto, ex.: {{\"modo\": \"auto\", \"voz\": \"pf_dora\"}}")
    check_keys(voices, VOICE_KEYS, f"{where}.falas")
    spec.voices = VoiceSpec(
        mode=_choice(voices.get("modo", "auto"), VOICE_MODES, f"{where}.falas.modo"),
        voice=_text(voices["voz"], f"{where}.falas.voz") if "voz" in voices else None,
        narrator=_text(voices["narrador"], f"{where}.falas.narrador") if "narrador" in voices else None,
        speed=_positive_float(voices.get("velocidade", 1.0), f"{where}.falas.velocidade"),
        volume=_non_negative(voices.get("volume", 1.0), f"{where}.falas.volume"),
        bip=_non_negative(voices.get("bip", 0.35), f"{where}.falas.bip"),
    )
    duck = raw.get("abafar", DUCK)
    if isinstance(duck, bool) or not isinstance(duck, (int, float)) or not 0 <= duck <= 1:
        raise SceneError(f"{where}.abafar: esperado número entre 0 e 1 (trilha durante as falas), não {duck!r}")
    spec.duck = float(duck)
    spec.volume = _non_negative(raw.get("volume", 1.0), f"{where}.volume")
    return spec


def parse_effects(raw, label: str, shot_where: str = "") -> list[Effect]:
    if not isinstance(raw, list):
        raise SceneError(f"{label}: esperado lista, ex.: [{{\"tipo\": \"chuva\"}}]")
    return [parse_effect(e, f"{label}[{i + 1}]", shot_where) for i, e in enumerate(raw)]


def parse_effect(raw, label: str, shot_where: str = "") -> Effect:
    if isinstance(raw, str):
        raw = {"tipo": raw}
    if not isinstance(raw, dict) or "tipo" not in raw:
        raise SceneError(f"{label}: esperado objeto com 'tipo' ({', '.join(EFFECTS)})")
    kind = raw["tipo"]
    if kind not in EFFECTS:
        raise SceneError(f"{label}.tipo: '{kind}' não existe; use {', '.join(EFFECTS)}")
    defaults = EFFECTS[kind]
    check_keys(raw, ("tipo", "inicio", "dur", *defaults), f"{label} ({kind})")
    params = {k: (_color(v, k) if k == "cor" and v is not None else v) for k, v in defaults.items()}
    for key, value in raw.items():
        if key in defaults:
            params[key] = _effect_value(kind, key, value, f"{label}.{key}")
    if kind == "luz" and params["pos"] is None:
        raise SceneError(f"{label}.pos: a luz precisa de 'pos' [x, y] (px do cenário)")
    if kind == "flash" and "dur" not in raw:
        raw = {**raw, "dur": 0.3}
    return Effect(
        kind, params, f"{shot_where}, {label}" if shot_where else label,
        start=_non_negative(raw.get("inicio", 0), f"{label}.inicio"),
        dur=_positive_float(raw["dur"], f"{label}.dur") if "dur" in raw else None,
    )


def _effect_value(kind: str, key: str, value, where: str):
    if key == "cor":
        return None if value is None else _color(value, where)
    if key == "pos":
        return _point(value, where)
    if key == "estilo":
        return _choice(value, PARTICLE_STYLES, where)
    if key == "modo":
        return _choice(value, TINT_MODES, where)
    if key in ("quantidade", "raio", "vento"):
        if isinstance(value, bool) or not isinstance(value, int) or not -400 <= value <= 400:
            raise SceneError(f"{where}: esperado inteiro, não {value!r}")
        if key != "vento" and value < 1:
            raise SceneError(f"{where}: esperado inteiro >= 1, não {value!r}")
        return value
    if key == "velocidade":
        return _non_negative(value, where)
    # intensidade, piscar: 0–1
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise SceneError(f"{where}: esperado número entre 0 e 1, não {value!r}")
    return float(value)


def parse_transition(raw, where: str) -> Transition:
    if isinstance(raw, str):
        raw = {"tipo": raw}
    if not isinstance(raw, dict):
        raise SceneError(f"{where}: use um nome ({' | '.join(TRANSITIONS)}) ou {{\"tipo\": ..., \"dur\": s}}")
    check_keys(raw, TRANSITION_KEYS, where)
    kind = raw.get("tipo", "corte")
    if kind not in TRANSITIONS:
        raise SceneError(f"{where}: transição '{kind}' inválida; use {' | '.join(TRANSITIONS)}")
    return Transition(
        kind,
        _positive_float(raw["dur"], f"{where}.dur") if "dur" in raw else FADE_DUR,
        _positive_int(raw["degraus"], f"{where}.degraus", maximum=32) if "degraus" in raw else FADE_STEPS,
        _color(raw["cor"], f"{where}.cor") if "cor" in raw else None,
    )


def parse_resolution(value, presets: dict | None) -> tuple[int, int]:
    """Nome de preset, "LxA" ou [L, A]. Sem `presets`, só valida o formato."""
    where = "resolucao"
    if isinstance(value, str):
        match = re.fullmatch(r"\s*(\d+)\s*[x×X]\s*(\d+)\s*", value)
        if match:
            value = [int(match[1]), int(match[2])]
        elif presets is None:
            return (0, 0)
        else:
            known = {k.lower(): v for k, v in presets.items()}
            if value.lower() not in known:
                raise SceneError(f"{where}: preset '{value}' não existe. Disponíveis: {', '.join(presets)}"
                                 " (ou use \"LxA\" / [L, A])")
            value = known[value.lower()]
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in value)):
        raise SceneError(f"{where}: use nome de preset, \"LxA\" ou [L, A], não {value!r}")
    w, h = value
    if not (8 <= w <= 1920 and 8 <= h <= 1080):
        raise SceneError(f"{where}: {w}x{h} fora do intervalo (8–1920 × 8–1080)")
    return (w, h)


def check_keys(raw: dict, valid: tuple[str, ...], where: str) -> None:
    for key in raw:
        if key.startswith("_") or key in valid:
            continue
        future = f" — {FUTURE[key]} ainda não está no motor" if key in FUTURE else ""
        raise SceneError(f"campo '{key}' desconhecido em {where}{future}. Campos válidos: {', '.join(valid)}")


# --------------------------------------------------------------------------


def _name(value, path: Path | None) -> str:
    if value is None:
        return path.stem if path else "cena"
    if not isinstance(value, str) or not re.fullmatch(r"[\w.-]+", value):
        raise SceneError(f"name: use letras, números, '-', '_' ou '.', não {value!r}")
    return value


def _backdrop_ref(value, where: str):
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, dict):
        return value
    raise SceneError(f"{where}: caminho da arte/cenário (ex.: \"cenarios/patio\") ou objeto com 'camadas'")


def _color(value, where: str) -> RGB:
    try:
        r, g, b, _ = parse_color(value)
    except (ValueError, TypeError) as exc:
        raise SceneError(f"{where}: {exc}") from None
    return (r, g, b)


def _point(value, where: str) -> tuple[int, int]:
    if (isinstance(value, (list, tuple)) and len(value) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in value)):
        return (value[0], value[1])
    raise SceneError(f"{where}: esperado [x, y] com inteiros (pixel inteiro), não {value!r}")


def _choice(value, options: tuple[str, ...], where: str) -> str:
    if value not in options:
        raise SceneError(f"{where}: '{value}' inválido; use {' | '.join(options)}")
    return value


def _text(value, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SceneError(f"{where}: esperado texto, não {value!r}")
    return value


def _label(value, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SceneError(f"{where}: esperado texto (\"\" esconde o nome)")
    return value


def _positive_float(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise SceneError(f"{where}: esperado número > 0 (segundos), não {value!r}")
    return float(value)


def _non_negative(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise SceneError(f"{where}: esperado número >= 0, não {value!r}")
    return float(value)


def _positive_int(value, where: str, maximum: int = 64) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise SceneError(f"{where}: esperado inteiro entre 1 e {maximum}, não {value!r}")
    return value
