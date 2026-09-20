# Current UI layout reference

## Purpose

This document records the current position, size, and shape values for the native dashboard.
It describes the implementation in `stay-watch/src/ui.rs`.
It is not a future design target.

The Rust UI uses Win32 client-area coordinates. It does not use CSS or a global padding value.
A `RECT` value defines each area with `left`, `top`, `right`, and `bottom` boundaries.
The source code is the final source of truth.

## Main layout

The main layout is in `dashboard_layout` at `stay-watch/src/ui.rs:323-357`.

| Reference | Current value | Effect |
|---|---:|---|
| `margin` | `8` | Outer left, right, and bottom space. |
| `gap` | `4` | Space between compact header areas. |
| `content_top` | `72` | Top of the card area below the header. |
| Header height | `64` | Fixed height of the custom dashboard header. |
| `splitter_width` | `16` | Width of the center splitter area. |
| Split range | `25` to `75` | Limits the upper card width ratio. |
| Initial split | `50` | Initial upper card width ratio. |

The available content width is the client width minus two `margin` values.
The process cards use the selected split ratio.
The header uses `gap` between the activity labels, idle panel, and Stop button.

The layout also applies minimum values during resize:

- `content_bottom` keeps at least `content_top + 220`.
- `pane_bottom` equals `content_bottom`.
- `pane_width` keeps at least `2` before the split calculation.
- `left_width` keeps at least `1`.

These limits prevent invalid rectangles when the window becomes small.
The window also has a separate minimum track size.

## Main rectangles

For a client rectangle with origin `(0, 0)`, the layout creates these areas:

- `helper_card`: left process card.
- `monitor_card`: right process card.
- `splitter`: the 16-pixel center area between the process cards.
- `activity_header`: compact activity labels inside the custom header.
- `idle_panel`: compact idle timer inside the custom header.
- `stop_button`: compact Stop control inside the custom header.

The process cards start at `content_top` and end at `content_bottom`.
The outer card areas have an 8-pixel left, right, and bottom margin.

## Process cards

The process cards use `draw_process_card` at `stay-watch/src/ui.rs:453-483`.
The common card shell is in `draw_card_shell` at `:447-451`.

### Card shell

- The card is a rounded rectangle.
- The corner radius is `8`.
- The border is one pixel wide.
- The header fill starts one pixel inside the card.
- The header rectangle ends at `area.top + 48`.

### Title and PID areas

- The title area starts 10 pixels from the left.
- The title area ends 10 pixels from the right.
- The title area starts 7 pixels below the card top.
- The title area ends at `area.top + 40`.
- The title font size is `18`.
- The PID label starts 10 pixels from the left.
- The PID label ends 34 pixels above the card bottom.
- The PID label area ends at `area.left + 52`.
- The PID value starts at `area.left + 54`.
- The PID value ends 10 pixels from the right.
- Both PID areas end 12 pixels above the card bottom.
- The PID font size is `14`.

The label-to-value space is 2 pixels between the two text rectangles.
The painted text uses single-line and vertical-center alignment.

### Output areas

The two output rectangles are in `dashboard_layout` at `:345-346`.

- `helper_output` is inside `helper_card`.
- `monitor_output` is inside `monitor_card`.
- Each output area has 6 pixels of left and right space.
- Each output area starts 50 pixels below its card top.
- Each output area ends 40 pixels above its card bottom.

The 50-pixel top inset leaves space for the smaller card header.
The native `EDIT` controls add their own client edge and Windows default text inset.
The code does not set `EM_SETMARGINS` or `EM_SETRECT`.

## Header

The header is in `draw_header` at `stay-watch/src/ui.rs:549-583`.

- The header fill is 64 pixels high.
- The separator is drawn from y `63` to y `65`.
- The green status box is 30 by 30 pixels.
- Its position is `(20, 16)`.
- Its corner radius is `6`.
- The `stay-up is` text uses the area `(66, 4, 154, 30)`.
- The `RUNNING` text uses the area `(156, 4, 246, 30)`.
- The `RUNNING` text uses the green status color.
- Both text areas use font size `15`.

The status box ends at x `50`. The `stay-up is` text starts at x `66`.
This keeps 16 pixels between the status box and the title.

## Header-integrated controls

The activity labels, idle timer, and Stop button are inside the custom header.
The header height remains 64 pixels.

### Activity labels

The activity labels are in `draw_header_activity` at `stay-watch/src/ui.rs:485-509`.

- The activity area starts at x `66`.
- It starts at y `30`, below the status text.
- It ends 4 pixels before the idle panel.
- Each label has a blue 6 by 6 pixel dot.
- The labels are `keyboard`, `mouse`, and `touchpad`.
- The label font size is `9`.
- The label groups use widths `58`, `48`, and `62` pixels.
- The gap between groups is 4 pixels.

### Idle timer

The idle timer is in `draw_header_idle` at `stay-watch/src/ui.rs:511-547`.

- The panel width is `170` pixels.
- The panel height is `32` pixels.
- The panel starts at y `16`.
- The panel ends at y `48`.
- The corner radius is `6`.
- The `IDLE:` text uses size `10`.
- The timer text uses size `18`.

### Stop button

The Stop button is in the header at `stay-watch/src/ui.rs:341-344`.
Its custom drawing is in `draw_stop_button` at `:765-827`.
Hover detection is in `stop_button_hovered` at `:751-763`.

- The button width is `108` pixels.
- The button height is `32` pixels.
- Its top boundary is y `16`.
- Its bottom boundary is y `48`.
- Its corner radius is `6`.
- The white stop icon is 14 by 14 pixels.
- The Stop text uses size `18`.
- The normal button fill is red.
- The Stop text is black on hover and white otherwise.
- The focus frame is inset by 2 pixels on every side.

## Splitter

The splitter is in `stay-watch/src/ui.rs:617-625` and `:1053-1100`.

- The painted splitter area is 16 pixels wide.
- The `Split` label uses a 22-pixel-high area.
- The label is centered.
- The label font size is `11`.
- The track control starts 20 pixels below the splitter top.
- The track control uses the vertical, no-tick style.
- The position range is `25` to `75`.
- The initial position is `50`.

A splitter change recalculates the two upper card widths.
The resize path calls `layout_controls` for the child controls at `:693-743`.

## Window size and resize

The main window is created at `stay-watch/src/ui.rs:952-965`.

- Initial size: `800` by `340`.
- Minimum track size: `800` by `340` at `stay-watch/src/ui.rs:831-835`.

`WM_SIZE` calls `layout_controls` and repaints the dashboard.
The child controls receive the current rectangles after each resize.
The initial child size of `10` by `10` is temporary.
The layout code replaces it before the window is shown.

## Text white space

Text line breaks affect white space inside the output panes.
They do not change the pane rectangles.

- `stay-watch/src/ui.rs:701-705` inserts one blank line after the log path.
- `stay-watch/src/output.rs:41-44` converts line endings to Windows CRLF format.
- `stay-watch/src/output.rs:148-155` adds a separator before additional output or errors.
- `stay-watch/src/output.rs:56-57` adds line breaks around read errors.
- `keep-awake.py:72-73` prints one line for each startup message.
- `monitor-helper.py:11-15` writes one newline after each heartbeat record.

## Source map

Use these source areas when a visual change is required:

| Visual part | Source reference |
|---|---|
| Main positions and sizes | `stay-watch/src/ui.rs:323-357` |
| Card shell and process text | `stay-watch/src/ui.rs:447-483` |
| Activity labels | `stay-watch/src/ui.rs:485-509` |
| Idle timer | `stay-watch/src/ui.rs:511-547` |
| Header and splitter label | `stay-watch/src/ui.rs:549-614` |
| Child control positions | `stay-watch/src/ui.rs:697-747` |
| Stop button hover and shape | `stay-watch/src/ui.rs:751-827` |
| Window minimum size | `stay-watch/src/ui.rs:831-835` |
| Native control styles | `stay-watch/src/ui.rs:999-1109` |
| Output text line breaks | `stay-watch/src/output.rs:41-155` |
