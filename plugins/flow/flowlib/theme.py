"""Design tokens read from ``theme.json``, and the icon library read from ``icons.json``."""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from .model import DEFAULT_THEME, Animation, LabelKind, Role, Shape, Status, Tone

DATA_DIR = Path(__file__).parent
WIRE_PAIR_KEYS = ("device", "responsive")  # the wireframe sizes written as [width, height]
THEMES_KEY = "themes"  # in ``theme.json``: the overrides of each theme other than the default
SHAPE_PAINT_KEY = "shape_paint"  # an override that paints every shape the same way
ICON_STROKE_WIDTH = 2  # line weight of a flat icon, in its 24 px grid
DFD_SIZE_KEYS = (
    "process_size",
    "entity_size",
    "store_size",
    "card_process_size",
    "card_entity_size",
    "card_store_size",
    "context_process_size",
)  # the fields of ``DfdRules`` that are a (width, height) pair in ``theme.json``
BPMN_SIZE_KEYS = ("task_size", "data_store_size")
C4_SIZE_KEYS = ("box_size", "system_size")
CLOUD_SIZE_KEYS = ("part_size",)
ARCHITECTURE_SIZE_KEYS = ("part_size", "card_size")
EXPLAINER_PROFILE_NAMES = ("standard", "compact")
EXPLAINER_SIZE_KEYS = (
    "card_size",
    "branch_size",
    "row_size",
    "head_size",
    "cell_size",
    "label_size",
    "vs_size",
    "fact_size",
    "hub_size",
    "root_size",
)  # the fields of ``ExplainerProfile`` that are a (width, height) pair in ``theme.json``
UML_SIZE_KEYS = ("state_size", "case_size", "actor_size", "actor_card_size")
GANTT_SIZE_KEYS = ("today_pill", "legend_swatch")
ORG_SIZE_KEYS = ("card", "card_illustrated", "works_pill")
ROADMAP_SIZE_KEYS = ("lane_head",)
MIND_SIZE_KEYS = ("centre", "branch", "group", "idea", "detail")
MIND_SCALE_NAMES = ("illustrated", "plain", "large")


@dataclass(frozen=True)
class Fonts:
    """Font family names."""

    sans: str
    mono: str


@dataclass(frozen=True)
class ShapeColors:
    """Fill and outline colour of a node shape."""

    fill: str
    stroke: str
    dash: str = ""  # an SVG dash pattern, or nothing for a solid outline
    stroke_width: float = 2  # outline weight in pixels, set by the theme
    radius: float = 10  # corner radius of a rounded box in pixels, set by the theme


@dataclass(frozen=True)
class ToneColors:
    """The tints, outline, accent and text colour of a tone."""

    box: str
    pill: str
    stroke: str
    accent: str
    lane: str
    label: str  # text on the pill tint, such as a key chip; the accent where that reads well


@dataclass(frozen=True)
class ChipColors:
    """Background and text colour of a chip."""

    background: str
    foreground: str


@dataclass(frozen=True)
class LineStyle:
    """How one line role is drawn. Sizes are in pixels; the arrowhead scales with ``width``."""

    color: str
    dash: str | None
    width: float
    head_size: float
    gap: float
    animation: Animation | None


@dataclass(frozen=True)
class AnimationSpeed:
    """One animated tier: how far the dashes move per cycle and how long a cycle lasts."""

    dash_offset: float
    seconds: float
    drawio_width: float  # draw.io ``strokeWidth`` of a line in this tier (design 01 section 6.3)
    drawio_duration_ms: int  # draw.io ``flowAnimationDuration`` of a line in this tier


@dataclass(frozen=True)
class StyleRules:
    """The parts of a theme that are not colours."""

    corner_radius: float
    frame_radius: float
    stroke_width: float
    shadow: bool


@dataclass(frozen=True)
class TextStyle:
    """Size in points and weight of one step of the type scale."""

    size: float
    weight: int


@dataclass(frozen=True)
class TypeScale:
    """The type scale of design 01 section 2."""

    title: TextStyle
    pill: TextStyle
    node: TextStyle
    edge: TextStyle
    mono: TextStyle


@dataclass(frozen=True)
class LayoutRules:
    """Sizes and gaps the layout follows. Lengths are in pixels."""

    min_sizes: dict[Shape, tuple[float, float]]
    max_node_width: float
    gap_vertical: float
    gap_vertical_labelled: float
    gap_horizontal: float
    gap_horizontal_labelled: float
    margin: float
    table_header_height: float
    table_row_height: float
    table_section_gap: float
    table_min_width: float
    table_row_gap: float
    table_padding_x: float
    table_bottom_pad: float
    table_extra_width: float
    table_card_header_height: float
    table_stereotype_height: float
    table_chip_width: float
    table_chip_gap: float
    table_key_columns: int
    table_name_font_size: float
    detail_font_size: float
    detail_line_height: float
    caption_height: float
    zone_padding: float
    zone_label_room: float
    lane_padding: float
    lane_tab: float
    fold_extent: float
    band_gap: float
    lane_min_size: float
    min_canvas_width: float
    title_block_height: float
    channel_offset: float
    channel_step: float
    label_offset: float
    char_width_em: float
    line_padding: float
    max_text_lines: int
    chip_font_size: float
    chip_height: float
    chip_padding_x: float
    chip_char_width_em: float
    card_min_width: float
    card_padding: float
    card_disc: float
    card_gap: float
    card_pill_height: float
    card_pill_padding: float
    card_icon_fraction: float
    fork_overhang: float
    fold_extent_lanes: float
    lane_size_plain: float
    lane_size_card: float


@dataclass(frozen=True)
class SequenceRules:
    """Sizes and gaps of a sequence diagram. Lengths are in pixels."""

    participant_width: float
    participant_height: float
    pitch: float
    min_gap_between_boxes: float
    first_message_gap: float
    row_height: float
    self_row_extra: float
    label_rise: float
    bar_width: float
    bar_overshoot: float
    bar_step: float
    fragment_enter: float
    fragment_exit: float
    fragment_pad_x: float
    fragment_inset_x: float
    divider_gap: float
    max_fragment_depth: int
    note_width: float
    note_offset: float
    note_line_height: float
    note_padding: float
    lost_length: float
    self_width: float
    self_height: float
    destroy_size: float
    tail_gap: float
    bottom_gap: float
    fragment_rise: float
    fragment_below_line: float
    header_card_width: float
    header_card_height: float
    header_pill_height: float
    header_pill_margin: float
    header_icon_top: float
    header_icon_size: float


@dataclass(frozen=True)
class DfdRules:
    """Sizes and gaps of a data flow diagram (design 14 sections 5 and 6). Lengths are in pixels."""

    process_size: tuple[float, float]
    entity_size: tuple[float, float]
    store_size: tuple[float, float]
    card_process_size: tuple[float, float]
    card_entity_size: tuple[float, float]
    card_store_size: tuple[float, float]
    context_process_size: tuple[float, float]
    column_pitch: float
    row_pitch: float
    card_column_pitch: float
    card_row_pitch: float
    strip_height: float
    id_cell_width: float
    pair_gap: float
    label_room: float
    frame_pad_x: float
    frame_pad_top: float
    frame_pad_bottom: float
    channel_step: float
    channel_clearance: float
    id_font_size: float
    entity_id_font_size: float
    entity_icon: float
    entity_text_left: float
    store_text_left: float
    card_strip_icon: float
    frame_pill_height: float
    frame_pill_inset: float
    min_flow_length: float


@dataclass(frozen=True)
class C4Rules:
    """Sizes and gaps of a C4 diagram (design 12). Lengths are in pixels."""

    box_size: tuple[float, float]
    system_size: tuple[float, float]
    column_pitch: float
    row_pitch: float
    pair_gap: float
    channel_step: float
    channel_clearance: float
    frame_pad: float
    frame_pad_bottom: float
    icon_size: float
    padding: float
    name_font_size: float
    tech_font_size: float
    text_font_size: float
    text_line_height: float
    text_left: float
    name_top: float
    text_top: float


@dataclass(frozen=True)
class UmlRules:
    """Sizes and gaps of the three UML diagrams (design 09). Lengths are in pixels."""

    state_size: tuple[float, float]
    state_dot: float
    state_gap_labelled: float
    state_gap_mark: float
    state_row_pitch: float
    state_column_pitch: float
    state_loop_height: float
    state_loop_span: float
    state_frame_pad_x: float
    state_frame_pad_top: float
    state_frame_pad_bottom: float
    state_activity_line_height: float
    case_size: tuple[float, float]
    case_column_pitch: float
    case_row_pitch: float
    actor_size: tuple[float, float]
    actor_card_size: tuple[float, float]
    actor_distance: float
    system_pad_x: float
    system_pad_top: float
    system_pad_bottom: float
    class_width: float
    class_column_pitch: float
    class_row_pitch: float
    pair_gap: float
    channel_step: float
    channel_clearance: float


@dataclass(frozen=True)
class StatusColors:
    """The colours of a task status: the bar, its outline and its second cue."""

    fill: str
    stroke: str
    mark: str  # the check of a done bar, the progress fill, the reason of a blocked bar


@dataclass(frozen=True)
class MarkColors:
    """A background and a text colour of a small mark on an idea of a mind map."""

    fill: str
    text: str


@dataclass(frozen=True)
class MilestoneColors:
    """The fill and the outline of the diamond of a milestone."""

    fill: str
    stroke: str


@dataclass(frozen=True)
class GanttRules:
    """Sizes of a Gantt chart (design 08 section 2). Lengths are in pixels."""

    week_width: float
    label_column: float
    row_height: float
    bar_height: float
    bar_inset: float
    bar_radius: float
    band_height: float
    month_height: float
    week_height: float
    header_radius: float
    person_size: float
    milestone_size: float
    dependency_gap: float
    label_pad: float
    person_gap: float
    today_pill: tuple[float, float]
    today_gap: float
    legend_gap: float
    legend_swatch: tuple[float, float]
    legend_item_gap: float
    max_rows: int
    grid_top_gap: float
    name_font_size: float
    week_font_size: float
    month_font_size: float
    reason_gap: float
    check_size: float


@dataclass(frozen=True)
class OrgRules:
    """Sizes of an org chart (design 08 section 3). Lengths are in pixels."""

    card: tuple[float, float]
    card_illustrated: tuple[float, float]
    level_pitch: float
    level_pitch_illustrated: float
    card_pitch: float
    subtree_gap: float
    bus_drop: float
    person_size: float
    max_levels: int
    pill_height: float
    icon_size: float
    pad: float
    name_font_size: float
    role_font_size: float
    works_pill: tuple[float, float]
    open_opacity: float
    legend_gap: float
    legend_line: float


@dataclass(frozen=True)
class KanbanRules:
    """Sizes of a Kanban board (design 08 section 5). Lengths are in pixels."""

    column_width: float
    column_gap: float
    column_radius: float
    pad: float
    header_top: float
    pill_height: float
    pill_pad: float
    pill_font_size: float
    badge_height: float
    badge_min_width: float
    badge_pad: float
    badge_font_size: float
    badge_gap: float
    cards_top: float
    card_height: float
    card_gap: float
    card_radius: float
    card_pad: float
    title_font_size: float
    detail_font_size: float
    title_top: float
    title_lines: int
    tag_height: float
    tag_font_size: float
    tag_pad: float
    tag_bottom: float
    tag_radius: float
    owner_size: float
    owner_right: float
    owner_bottom: float
    done_opacity: float
    bottom_pad: float


@dataclass(frozen=True)
class RoadmapRules:
    """Sizes of a roadmap (design 08 section 6). Lengths are in pixels."""

    lane_head: tuple[float, float]
    lane_head_gap: float
    lane_gap: float
    lane_pad: float
    card_height: float
    card_inset: float
    row_gap: float
    card_radius: float
    card_pad: float
    column_max: float
    column_min: float
    column_budget: float
    column_gap: float
    period_height: float
    period_radius: float
    period_font_size: float
    period_detail_font_size: float
    period_gap: float
    title_font_size: float
    title_top: float
    tag_top: float
    tag_gap: float
    detail_font_size: float
    lane_icon_size: float
    lane_icon_top: float
    lane_pill_height: float
    lane_pill_pad: float
    lane_pill_font_size: float
    lane_pill_bottom: float
    note_gap: float
    note_font_size: float
    entry_run: float
    exit_gap: float
    exit_drop: float
    entry_offset: float
    owner_size: float
    owner_right: float
    owner_bottom: float


@dataclass(frozen=True)
class MindScale:
    """Sizes of one scale of mind map: illustrated, plain, or the large one with four levels."""

    centre: tuple[float, float]
    branch: tuple[float, float]
    group: tuple[float, float]
    idea: tuple[float, float]
    detail: tuple[float, float]
    centre_gap: float
    column_gap: float
    row_gap: float
    subtree_gap: float
    branch_pitch: float
    branch_font: float
    group_font: float
    idea_font: float
    detail_font: float
    disc: float
    leaf_icon: float


@dataclass(frozen=True)
class MindRules:
    """Sizes and limits of a mind map (design 08 section 4)."""

    illustrated: MindScale
    plain: MindScale
    large: MindScale
    person_size: float
    owner_size: float
    max_leaf_words: int
    max_links: int
    link_bulge: float
    link_pill_gap: float
    bar_width: float
    centre_pill_height: float


@dataclass(frozen=True)
class PlanningRules:
    """The colours and sizes of the planning diagrams (design 08)."""

    status: dict[Status, StatusColors]
    marks: dict[str, MarkColors]
    milestone: MilestoneColors
    accents: dict[Tone, str]  # the strong colour of each tone in a mind map: pills, bars, curves
    gantt: GanttRules
    kanban: KanbanRules
    roadmap: RoadmapRules
    org: OrgRules
    mind: MindRules


@dataclass(frozen=True)
class CloudRules:
    """Sizes and gaps of a cloud diagram (design 13). Lengths are in pixels."""

    part_size: tuple[float, float]
    row_pitch: float
    column_pitch: float
    frame_gap: float
    part_pad: float
    pair_gap: float
    channel_step: float
    channel_clearance: float
    pill_height: float
    pill_inset: float
    site_offset: float
    edge_row: int
    public_row: int
    private_row: int
    data_row: int
    tint_alpha: float
    border_width: float


@dataclass(frozen=True)
class ArchitectureRules:
    """Sizes and gaps of an architecture diagram (design 06). Lengths are in pixels."""

    part_size: tuple[float, float]
    card_size: tuple[float, float]
    layer_pitch: float
    card_layer_pitch: float
    column_pitch: float
    card_column_pitch: float
    frame_gap: float
    pair_gap: float
    channel_step: float
    channel_clearance: float
    card_icon_size: float


@dataclass(frozen=True)
class ExplainerProfile:
    """The sizes of one scale of an explainer: a page of its own, or a section beside others."""

    card_size: tuple[float, float]
    band_height: float
    band_pitch: float
    band_card_top: float
    col_offset: float
    col_pitch: float
    branch_size: tuple[float, float]
    branch_icon: float
    row_size: tuple[float, float]
    row_icon: float
    row_pitch: float
    head_size: tuple[float, float]
    cell_size: tuple[float, float]
    label_size: tuple[float, float]
    vs_size: tuple[float, float]
    compare_pitch: float
    compare_gap: float
    compare_spread: float
    fact_size: tuple[float, float]
    hub_size: tuple[float, float]
    root_size: tuple[float, float]


@dataclass(frozen=True)
class ExplainerRules:
    """Sizes, gaps and type of an explainer (design 07). Lengths are in pixels."""

    title_size: float
    title_top: float
    title_height: float
    description_size: float
    description_line_height: float
    description_height: float
    description_max_width: float
    canvas_width: float
    narrow_width: float
    left_column_width: float
    right_column_width: float
    page_margin: float
    bottom_margin: float
    column_gap: float
    section_gap: float
    section_head_size: float
    section_head_font: float
    section_head_gap: float
    section_head_letter_font: float
    first_section_top: float
    layers_top: float
    tree_top: float
    compare_top: float
    concept_top: float
    card_icon_size: float
    card_icon_top: float
    card_pill_top: float
    card_pill_height: float
    card_pill_font: float
    card_detail_top: float
    card_detail_font: float
    card_detail_line: float
    card_pad: float
    card_radius: float
    border_width: float
    pill_shadow: float
    pill_pad: float
    badge_size: float
    badge_overhang: float
    badge_font: float
    row_icon_inset: float
    row_name_font: float
    row_detail_gap: float
    row_detail_font: float
    row_radius: float
    chip_height: float
    chip_font: float
    chip_gap: float
    chip_pad: float
    chips_label_font: float
    cell_font: float
    cell_pad: float
    cell_radius: float
    label_font: float
    vs_font: float
    remark_font: float
    remark_gap: float
    closing_gap: float
    note_font: float
    note_gap: float
    rule_title_font: float
    rule_text_font: float
    rule_pad: float
    rule_height: float
    rule_gap: float
    rule_title_top: float
    rule_text_top: float
    band_radius: float
    band_pill_left: float
    band_pill_top: float
    band_pill_height: float
    band_pill_font: float
    band_alpha: float
    band_pill_pad: float
    analogy_card_top: float
    analogy_bottom: float
    stack_gap: float
    label_gap: float
    tree_root_inset: float
    tree_bus_gap: float
    concept_spread: float
    concept_row_pitch: float
    hub_line_offset: float
    rule_line_extend: float
    standard: ExplainerProfile
    compact: ExplainerProfile


@dataclass(frozen=True)
class BpmnRules:
    """Sizes and gaps of a BPMN diagram (design 11 section 7). Lengths are in pixels."""

    event_radius: float
    task_size: tuple[float, float]
    gateway_width: float
    boundary_radius: float
    boundary_inset: float
    data_store_size: tuple[float, float]
    gap_plain: float
    gap_labelled: float
    pool_left: float
    band_width: float
    lane_min_height: float
    pool_gap: float
    row_pitch: float
    lane_pad: float
    black_box_height: float
    channel_step: float
    channel_clearance: float
    marker_extent: float
    task_marker_inset: float
    bottom_marker_gap: float
    caption_room: float
    label_gap: float
    data_store_drop: float
    stub: float
    content_pad: float
    pool_right_pad: float


@dataclass(frozen=True)
class ScreenRules:
    """Sizes, gaps and colours of a screen flow (design 02). Lengths are in pixels."""

    sizes: dict[str, tuple[float, float]]  # device frame sizes by name
    radius: dict[str, float]  # corner radius of each device frame
    border: float
    card_height: float
    decision: tuple[float, float]
    entry: tuple[float, float]
    flag: tuple[float, float]
    tab: tuple[float, float]
    gap: float
    gap_labelled: float
    channel_pitch: float
    channel_margin: float
    chip_room: float
    chip_height: float
    chip_padding: float
    chip_gap: float
    trigger_chip_height: float
    trigger_icon: float
    zone_pad_x: float
    zone_pad_top: float
    zone_pad_bottom: float
    zone_gap: float
    table_gap: float
    port_pitch: float
    port_clear: float
    inner_pad: float
    title_size: float
    text_size: float
    element_height: float
    element_gap: float
    element_radius: float
    bar_height: float
    bar_gap: float
    notch_width: float
    notch_height: float
    notch_top: float
    browser_bar: float
    illustration: float
    hotspot_radius: float
    halo_radius: float
    tab_height: float
    tab_dot: float
    hatch_stripe: float
    scrim_opacity: float
    halo_color: str
    hotspot_color: str
    dot_red: str
    dot_amber: str
    dot_green: str


@dataclass(frozen=True)
class WireColors:
    """The grey palette of a wireframe and its few accents (design 10 section 1)."""

    amber: str
    amber_tint: str
    bar: str
    blue: str
    blue_soft: str
    blue_tint: str
    chip_text: str
    chrome: str
    cross: str
    fill: str
    gray_tint: str
    green: str
    green_tint: str
    hairline: str
    image: str
    ink: str
    line: str
    muted: str
    on_blue: str
    paper: str
    rose: str
    rose_tint: str
    screen: str
    skeleton: str
    text: str


@dataclass(frozen=True)
class WireNotes:
    """The notes below the screens of a wireframe: badge, title and one line. Lengths in pixels."""

    title_font: float
    text_font: float
    pitch: float
    text_left: float
    max_lines: int
    column_gap: float
    notes_top: float
    screen_gap: float
    states_gap: float
    responsive_gap: float
    screens_left: float
    badge_size: float
    min_width: float
    columns: int
    line_height: float
    title_height: float


@dataclass(frozen=True)
class WireRules:
    """Sizes, gaps and type of the wireframe blocks, at the real size of a device (design 10)."""

    colors: WireColors
    notes: WireNotes
    device: dict[str, tuple[float, float]]
    radius: dict[str, float]
    margin: dict[str, float]
    gap: dict[str, float]
    section_gap: dict[str, float]
    content_top: dict[str, float]
    flow_scale: dict[str, float]
    responsive: dict[str, tuple[float, float]]
    address_height: float
    address_left: float
    address_pad: float
    address_width: float
    anchor_gap: float
    anchor_pad: float
    anchor_pad_nav: float
    avatar_icon: float
    avatar_size: float
    badge_ring: float
    badge_size: float
    bar_fraction: float
    bar_gap: float
    bar_headroom: float
    bar_height: float
    bar_radius: float
    bell_size: float
    border: float
    bottom_icon: float
    bottom_icon_top: float
    bottom_label_gap: float
    bottom_nav_height: float
    browser_bar: float
    browser_dot: float
    button_border: float
    button_font: float
    button_height: float
    button_height_phone: float
    button_icon: float
    button_radius: float
    caption_gap: float
    caption_height: float
    caption_note_height: float
    card_bar_title: float
    card_bar_top: float
    card_footer: float
    card_image: float
    card_pad: float
    card_radius: float
    card_row_height: float
    badge_gap: float
    price_pad: float
    tap_edge: float
    tap_narrow: float
    card_text_gap: float
    card_thumb: float
    card_thumb_bars: float
    chart_height: float
    chart_pad: float
    chart_top: float
    check_fraction: float
    check_gap: float
    check_radius: float
    check_size: float
    check_stroke: float
    checklist_row: float
    checklist_title: float
    chevron_inset: float
    chevron_stroke: float
    chip_font: float
    chip_gap: float
    chip_height: float
    chip_pad: float
    choice_font: float
    choice_gap: float
    choice_height: float
    choice_pad: float
    dot_amber: str
    dot_green: str
    dot_left: float
    dot_radius: float
    dot_red: str
    dot_ring: float
    dot_step: float
    empty_icon_fraction: float
    field_action_gap: float
    field_action_width: float
    figure_gap: float
    figure_height: float
    figure_pad: float
    font_badge: float
    font_body: float
    font_brand: float
    font_caption: float
    font_error_mark: float
    font_figure: float
    font_header: float
    font_heading: float
    font_hero: float
    font_hint: float
    font_label: float
    font_link: float
    font_nav: float
    font_navbar: float
    font_small: float
    font_state_title: float
    font_time: float
    font_title: float
    foot: float
    halo_radius: float
    hamburger_size: float
    hamburger_stroke: float
    handle_height: float
    handle_top: float
    handle_width: float
    hero_pad: float
    hero_narrow: float
    font_hero_small: float
    hint_gap: float
    home_bottom: float
    home_height: float
    home_width: float
    icon_gap: float
    image_height: float
    input_height: float
    input_pad: float
    input_radius: float
    item_gap: float
    item_height: float
    item_height_disc: float
    item_pad: float
    item_radius: float
    label_gap: float
    label_gap_below: float
    lead_icon: float
    lead_size: float
    line_factor: float
    link_gap: float
    logo_gap: float
    logo_radius: float
    logo_size: float
    mini_height: float
    mini_width: float
    modal_button: float
    modal_fraction: float
    modal_gap: float
    modal_pad: float
    modal_radius: float
    nav_action_height: float
    nav_action_width: float
    nav_gap: float
    nav_search_width: float
    navbar_height: float
    navbar_height_phone: float
    navbar_pad: float
    navbar_pad_phone: float
    radio_size: float
    radio_stroke: float
    row_height: float
    row_pad: float
    row_value_start: float
    scrim_opacity: float
    search_height: float
    search_icon: float
    search_pad: float
    selected_border: float
    sheet_foot: float
    sheet_radius: float
    sheet_row: float
    sheet_title: float
    sheet_top: float
    sidebar_icon: float
    sidebar_icon_pad: float
    sidebar_pad: float
    sidebar_pitch: float
    sidebar_row: float
    sidebar_text_gap: float
    sidebar_width: float
    skeleton_bar: float
    skeleton_bar_offset: float
    skeleton_disc: float
    skeleton_height: float
    spinner_gap: float
    spinner_room: float
    spinner_size: float
    spinner_stroke: float
    spinner_top: float
    state_button: float
    state_button_gap: float
    state_button_width: float
    state_gap: float
    state_icon: float
    state_text_pad: float
    state_top: float
    status_height: float
    stepper_height: float
    stepper_pad: float
    stepper_stroke: float
    stepper_width: float
    success_icon: float
    symbol_stroke: float
    tab_height: float
    tab_underline: float
    table_button_height: float
    table_button_width: float
    table_cell_pad: float
    table_header: float
    table_row: float
    table_title: float
    tap_inset: float
    thumb_radius: float
    time_left: float
    time_top: float
    time_width: float
    title_inset: float
    toast_height: float
    toast_lift: float
    toast_pad: float


@dataclass(frozen=True)
class Theme:
    """Every colour, line style and animation the renderers use."""

    name: str
    fonts: Fonts
    ink: str
    slate: str
    canvas: str
    paper: str  # the surface of a table body or a tag, which stands out from the canvas
    on_accent: str  # text on an accent colour, such as a lane tab
    rule: str  # a divider inside a table
    row_rule: str  # the lighter rule between two rows
    style: StyleRules
    type_scale: TypeScale
    drawio_weights: dict[float, float]  # canvas line width in px to draw.io ``strokeWidth``
    badge: ChipColors
    shapes: dict[Shape, ShapeColors]
    tones: dict[Tone, ToneColors]
    roles: dict[Role, LineStyle]
    animations: dict[Animation, AnimationSpeed]
    chips: dict[LabelKind, ChipColors]
    layout: LayoutRules
    sequence: SequenceRules
    screen: ScreenRules
    dfd: DfdRules
    bpmn: BpmnRules
    c4: C4Rules
    cloud: CloudRules
    architecture: ArchitectureRules
    explainer: ExplainerRules
    wire: WireRules
    uml: UmlRules
    planning: PlanningRules


def _line_style(raw: dict[str, Any]) -> LineStyle:
    """Build a line style from its JSON object.

    Args:
        raw: The JSON object of one role in ``theme.json``.

    Returns:
        The line style, with ``animation`` set to None for a role that does not move.
    """
    animation = raw.get("animation")
    return LineStyle(
        color=raw["color"],
        dash=raw["dash"],
        width=raw["width"],
        head_size=raw["head_size"],
        gap=raw["gap"],
        animation=Animation(animation) if animation else None,
    )


def _layout_rules(raw: dict[str, Any]) -> LayoutRules:
    """Build the layout rules from their JSON object.

    Args:
        raw: The ``layout`` object of ``theme.json``.

    Returns:
        The rules, with each minimum size as a ``(width, height)`` tuple.
    """
    sizes = {Shape(name): (size[0], size[1]) for name, size in raw["min_sizes"].items()}
    return LayoutRules(**{**raw, "min_sizes": sizes})


def _screen_rules(raw: dict[str, Any]) -> ScreenRules:
    """Build the screen flow rules from their JSON object.

    Args:
        raw: The ``screen`` object of ``theme.json``.

    Returns:
        The rules, with each size as a ``(width, height)`` tuple.
    """
    pairs = ("decision", "entry", "flag", "tab")
    sizes = {name: (size[0], size[1]) for name, size in raw["sizes"].items()}
    tuples = {name: (raw[name][0], raw[name][1]) for name in pairs}
    return ScreenRules(**{**raw, **tuples, "sizes": sizes})


def _wire_rules(raw: dict[str, Any]) -> WireRules:
    """Build the wireframe rules from their JSON object.

    Args:
        raw: The ``wire`` object of ``theme.json``.

    Returns:
        The rules, with the palette and the notes as objects and each size as a pair.
    """
    pairs = {name: {key: _pair(size) for key, size in raw[name].items()} for name in WIRE_PAIR_KEYS}
    loose = {
        key: value for key, value in raw.items() if key not in (*WIRE_PAIR_KEYS, "colors", "notes")
    }
    return WireRules(
        **loose, **pairs, colors=WireColors(**raw["colors"]), notes=WireNotes(**raw["notes"])
    )


def _pair(raw: list[float]) -> tuple[float, float]:
    """Turn a two-item JSON list into a ``(width, height)`` tuple."""
    return (raw[0], raw[1])


def _dfd_rules(raw: dict[str, Any]) -> DfdRules:
    """Build the data flow diagram rules; each ``*_size`` becomes a ``(width, height)`` tuple."""
    sizes = {key: _pair(raw[key]) for key in DFD_SIZE_KEYS}
    return DfdRules(**{**raw, **sizes})


def _bpmn_rules(raw: dict[str, Any]) -> BpmnRules:
    """Build the BPMN rules; each ``*_size`` becomes a ``(width, height)`` tuple."""
    sizes = {key: _pair(raw[key]) for key in BPMN_SIZE_KEYS}
    return BpmnRules(**{**raw, **sizes})


def _sized(raw: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Return a rules object with each of ``keys`` turned into a ``(width, height)`` tuple."""
    return {**raw, **{key: _pair(raw[key]) for key in keys}}


def _planning_rules(raw: dict[str, Any], tones: dict[Tone, ToneColors]) -> PlanningRules:
    """Build the planning rules; each size becomes a ``(width, height)`` tuple.

    Args:
        raw: The ``planning`` object of ``theme.json``.
        tones: The tones of the theme, whose accent a mind map uses unless the rules name one.

    Returns:
        The status colours, mark colours and the sizes of the three planning diagrams.
    """
    marks = {
        name: MarkColors(**colors) for name, colors in raw["marks"].items() if "text" in colors
    }
    mind = raw["mind"]
    scales = {name: MindScale(**_sized(mind[name], MIND_SIZE_KEYS)) for name in MIND_SCALE_NAMES}
    loose = {key: value for key, value in mind.items() if key not in MIND_SCALE_NAMES}
    return PlanningRules(
        status={Status(name): StatusColors(**colors) for name, colors in raw["status"].items()},
        marks=marks,
        milestone=MilestoneColors(**raw["marks"]["milestone"]),
        accents={
            tone: raw["accents"].get(tone.value, colors.accent) for tone, colors in tones.items()
        },
        gantt=GanttRules(**_sized(raw["gantt"], GANTT_SIZE_KEYS)),
        kanban=KanbanRules(**raw["kanban"]),
        roadmap=RoadmapRules(**_sized(raw["roadmap"], ROADMAP_SIZE_KEYS)),
        org=OrgRules(**_sized(raw["org"], ORG_SIZE_KEYS)),
        mind=MindRules(**loose, **scales),
    )


def _build_theme(name: str, raw: dict[str, Any]) -> Theme:
    """Build a theme from the parsed ``theme.json``, with a theme's overrides already merged.

    Args:
        name: The theme name.
        raw: The parsed JSON document.

    Returns:
        The theme. A key that is not a member of the matching enum raises ``ValueError``.
    """
    style = StyleRules(**raw["style"])
    paint = {"stroke_width": style.stroke_width, "radius": style.corner_radius}
    tones = {Tone(name): ToneColors(**colors) for name, colors in raw["tones"].items()}
    return Theme(
        name=name,
        fonts=Fonts(**raw["fonts"]),
        ink=raw["ink"],
        slate=raw["slate"],
        canvas=raw["canvas"],
        paper=raw["paper"],
        on_accent=raw["on_accent"],
        rule=raw["rule"],
        row_rule=raw["row_rule"],
        style=style,
        type_scale=TypeScale(
            **{key: TextStyle(**value) for key, value in raw["type_scale"].items()}
        ),
        drawio_weights={float(key): value for key, value in raw["drawio_weights"].items()},
        badge=ChipColors(**raw["badge"]),
        shapes={
            Shape(shape): ShapeColors(**colors, **paint) for shape, colors in raw["shapes"].items()
        },
        tones=tones,
        roles={Role(name): _line_style(style) for name, style in raw["roles"].items()},
        animations={
            Animation(name): AnimationSpeed(**speed) for name, speed in raw["animations"].items()
        },
        chips={LabelKind(name): ChipColors(**colors) for name, colors in raw["chips"].items()},
        layout=_layout_rules(raw["layout"]),
        sequence=SequenceRules(**raw["sequence"]),
        screen=_screen_rules(raw["screen"]),
        wire=_wire_rules(raw["wire"]),
        dfd=_dfd_rules(raw["dfd"]),
        bpmn=_bpmn_rules(raw["bpmn"]),
        c4=C4Rules(**_sized(raw["c4"], C4_SIZE_KEYS)),
        cloud=CloudRules(**_sized(raw["cloud"], CLOUD_SIZE_KEYS)),
        architecture=ArchitectureRules(**_sized(raw["architecture"], ARCHITECTURE_SIZE_KEYS)),
        explainer=_explainer_rules(raw["explainer"]),
        uml=UmlRules(**_sized(raw["uml"], UML_SIZE_KEYS)),
        planning=_planning_rules(raw["planning"], tones),
    )


def _explainer_rules(raw: dict[str, Any]) -> ExplainerRules:
    """Build the explainer rules; each profile has its sizes turned into pairs.

    Args:
        raw: The ``explainer`` object of ``theme.json``.

    Returns:
        The rules, with the ``standard`` and ``compact`` profiles.
    """
    profiles = {
        name: ExplainerProfile(**_sized(raw[name], EXPLAINER_SIZE_KEYS))
        for name in EXPLAINER_PROFILE_NAMES
    }
    loose = {key: value for key, value in raw.items() if key not in EXPLAINER_PROFILE_NAMES}
    return ExplainerRules(**loose, **profiles)


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return ``base`` with ``override`` laid over it, going into nested objects.

    Args:
        base: The settings to start from; not changed.
        override: The settings that win. A value that is not an object replaces the one in base.

    Returns:
        A new dict.
    """
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _merge(base[key], value)
        else:
            merged[key] = value
    return merged


def _paint_every_shape(raw: dict[str, Any], paint: dict[str, Any]) -> dict[str, Any]:
    """Give each shape one fill and outline colour, except the shapes the override names.

    Args:
        raw: The merged settings.
        paint: The ``shape_paint`` override: ``fill``, ``stroke`` and ``except``, a list of shapes.

    Returns:
        The settings with every shape repainted.
    """
    colors = {"fill": paint["fill"], "stroke": paint["stroke"]}
    kept = set(paint.get("except", ()))
    shapes = {name: (old if name in kept else colors) for name, old in raw["shapes"].items()}
    return {**raw, "shapes": shapes}


def theme_names() -> list[str]:
    """Return every theme name a spec may use, the default first."""
    raw = json.loads((DATA_DIR / "theme.json").read_text(encoding="utf-8"))
    return [DEFAULT_THEME, *raw[THEMES_KEY]]


@cache
def load_theme(name: str = DEFAULT_THEME) -> Theme:
    """Return a theme, read once from ``theme.json``.

    Args:
        name: One of ``theme_names()``. Every theme but the default is the default with the
            overrides listed under its name in ``theme.json``.

    Returns:
        The theme.

    Raises:
        KeyError: If the name is not a theme.
    """
    raw = json.loads((DATA_DIR / "theme.json").read_text(encoding="utf-8"))
    overrides = raw.pop(THEMES_KEY)
    if name == DEFAULT_THEME:
        return _build_theme(name, raw)
    override = dict(overrides[name])
    paint = override.pop(SHAPE_PAINT_KEY, None)
    merged = _paint_every_shape(raw, paint) if paint else raw
    return _build_theme(name, _merge(merged, override))


@cache
def _load_builtin_icons() -> dict[str, str]:
    """Return the icons that ship with the plugin."""
    return json.loads((DATA_DIR / "icons.json").read_text(encoding="utf-8"))


_LOCAL_ICONS: dict[str, str] = {}


@cache
def load_detailed_icons() -> dict[str, str]:
    """Return the detailed icons: name to the inner SVG of a 64 x 64 viewBox, with own colours."""
    return json.loads((DATA_DIR / "icons_detailed.json").read_text(encoding="utf-8"))


def icon_names() -> set[str]:
    """Return every icon name a spec may use: flat, custom and detailed."""
    return set(load_icons()) | set(load_detailed_icons())


def has_detailed_icon(name: str) -> bool:
    """Tell whether an icon has a detailed drawing."""
    return name in load_detailed_icons()


def icon_svg(name: str, size: float, stroke: str, attrs: str = "") -> str:
    """Draw an icon as an ``svg`` element, using the flat drawing when there is one.

    Args:
        name: An icon name from ``icon_names``.
        size: The drawn width and height in pixels.
        stroke: The line colour of a flat icon; a detailed icon has its own colours.
        attrs: Extra attributes for the element, such as a ``style`` or ``xmlns``.

    Returns:
        The ``svg`` element.
    """
    flat = load_icons().get(name)
    if flat is None:
        return detailed_icon_svg(name, size, stroke, attrs)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" {attrs} fill="none" '
        f'stroke="{stroke}" stroke-width="{ICON_STROKE_WIDTH}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{flat}</svg>'
    )


def detailed_icon_svg(name: str, size: float, stroke: str, attrs: str = "") -> str:
    """Draw an icon in its detailed form when it has one, else as the flat drawing.

    Args:
        name: An icon name from ``icon_names``.
        size: The drawn width and height in pixels.
        stroke: The line colour used when only a flat drawing exists.
        attrs: Extra attributes for the element, such as a ``style`` or ``xmlns``.

    Returns:
        The ``svg`` element.
    """
    detailed = load_detailed_icons().get(name)
    if detailed is None:
        return icon_svg(name, size, stroke, attrs)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" {attrs} '
        f'overflow="visible" aria-hidden="true">{detailed}</svg>'
    )


def register_icons(icons: dict[str, str]) -> None:
    """Add checked custom icons to the library for the rest of the run.

    Args:
        icons: Icon name to inner SVG markup; the caller has validated both.
    """
    _LOCAL_ICONS.update(icons)


def load_icons() -> dict[str, str]:
    """Return the simple line icons: name to the inner SVG of a 24 x 24 viewBox."""
    return {**_load_builtin_icons(), **_LOCAL_ICONS}
