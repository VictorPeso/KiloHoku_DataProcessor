"""Streamlit app for database-backed light-curve visualization."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from data_processor.config.settings import get_settings
from data_processor.infrastructure.database.repositories.light_curve_repository import (
    AstronomicalObjectSummary,
    LightCurveReadRepository,
)
from data_processor.infrastructure.database.session import session_scope

STYLE_PATH = Path(__file__).with_name("styles.css")

FILTER_COLORS = {
    "g": "#62d989",
    "r": "#ff5d5d",
    "i": "#ffd166",
}

FILTER_LABELS = {
    "g": "Green filter",
    "r": "Red filter",
    "i": "Infrared filter",
}

AXIS_OPTIONS = {
    "hjd": "Heliocentric Julian Date",
    "mjd": "Modified Julian Date",
    "magnitude": "Magnitude",
    "magnitude_error": "Magnitude uncertainty",
    "catalog_flags": "Catalog flags",
    "oid": "Object catalog identifier",
    "exposure_id": "Exposure identifier",
    "ra": "Right ascension",
    "dec": "Declination",
    "chi": "PSF fit chi statistic",
    "sharpness": "Sharpness",
    "file_fractional_day": "File fractional day",
    "field_id": "Survey field identifier",
    "ccd_id": "CCD identifier",
    "quadrant_id": "CCD quadrant identifier",
    "limiting_magnitude": "Limiting magnitude",
    "magnitude_zeropoint": "Magnitude zeropoint",
    "magnitude_zeropoint_rms": "Magnitude zeropoint RMS",
    "color_coefficient": "Color coefficient",
    "color_coefficient_uncertainty": "Color coefficient uncertainty",
    "exposure_time": "Exposure time",
    "airmass": "Airmass",
    "program_id": "Program ID",
}


def main() -> None:
    st.set_page_config(page_title="Light Curve Viewer", layout="wide")
    _inject_style()

    settings = get_settings()
    st.sidebar.caption("Preload folder")
    st.sidebar.code(settings.local_light_curves_path)
    st.sidebar.caption("The viewer reads from PostgreSQL, not directly from XML files.")

    if "selected_object_id" not in st.session_state:
        st.session_state.selected_object_id = None

    if st.session_state.selected_object_id is None:
        _render_object_list()
        return

    _render_object_detail(st.session_state.selected_object_id)


def _render_object_list() -> None:
    st.title("Light Curve Viewer")
    st.subheader("Astronomical Objects")
    st.caption("Objects are read from PostgreSQL and ordered by `source_name`.")

    try:
        objects = _load_ztf_objects()
    except Exception as exc:
        st.error(f"Could not read objects from PostgreSQL: {exc}")
        return

    if not objects:
        st.info("No ZTF objects were found in the database.")
        return

    search = st.text_input("Search object", value="", placeholder="ZTF...")
    filtered_objects = [
        astronomical_object
        for astronomical_object in objects
        if search.lower() in astronomical_object.source_name.lower()
    ]

    st.caption(f"{len(filtered_objects):,} object(s)")

    for astronomical_object in filtered_objects:
        columns = st.columns([4.2, 2.2, 1.8, 1.8, 1], vertical_alignment="center")
        columns[0].markdown(f"**{astronomical_object.source_name}**")
        columns[1].markdown(
            _render_filter_chips(_available_filters_from_summary(astronomical_object)),
            unsafe_allow_html=True,
        )
        columns[2].write(f"Series: {astronomical_object.series_count}")
        columns[3].write(f"Obs: {astronomical_object.observation_count:,}")
        if columns[4].button("Open", key=f"open-{astronomical_object.id}"):
            st.session_state.selected_object_id = astronomical_object.id
            st.rerun()


def _render_object_detail(object_id: int) -> None:
    object_name = _load_object_name(object_id)
    if object_name is None:
        st.error("Selected object no longer exists.")
        if st.button("Back to objects"):
            st.session_state.selected_object_id = None
            st.rerun()
        return

    st.title(object_name)
    if st.button("Back to objects"):
        st.session_state.selected_object_id = None
        st.rerun()

    available_filters = _load_available_filters(object_id)
    if not available_filters:
        st.warning("This object has no photometric series with filters g, r, or i.")
        return

    left_panel, chart_panel = st.columns([1.05, 3.2], gap="large")

    with left_panel:
        selected_filters, x_axis, y_axis, only_valid_observations = _render_control_panel(
            object_id=object_id,
            available_filters=available_filters,
        )

    if not selected_filters:
        chart_panel.info("Select at least one curve to display.")
        return

    try:
        dataframe = _load_light_curve(
            object_id=object_id,
            selected_filters=selected_filters,
            only_valid_observations=only_valid_observations,
        )
    except Exception as exc:
        chart_panel.error(f"Could not load light curve data from PostgreSQL: {exc}")
        return

    if dataframe.empty:
        chart_panel.warning("No observations match the selected filters.")
        return

    dataframe = _prepare_dataframe_for_plot(dataframe)
    missing_axes = [
        axis
        for axis in [x_axis, y_axis]
        if axis not in dataframe.columns or dataframe[axis].isna().all()
    ]
    if missing_axes:
        chart_panel.error(f"No usable values found for: {', '.join(missing_axes)}")
        return

    with chart_panel:
        _render_light_curve(
            dataframe=dataframe,
            object_name=object_name,
            x_axis=x_axis,
            y_axis=y_axis,
        )


def _render_control_panel(
    *,
    object_id: int,
    available_filters: list[str],
) -> tuple[list[str], str, str, bool]:
    selected_filters = _selected_filters_for_object(
        object_id=object_id,
        available_filters=available_filters,
    )

    with st.container(border=True):
        st.markdown("### Curves")

        for filter_code in ["g", "r", "i"]:
            disabled = filter_code not in available_filters
            selected = filter_code in selected_filters
            selected_filters = _render_filter_button(
                object_id=object_id,
                filter_code=filter_code,
                selected_filters=selected_filters,
                selected=selected,
                disabled=disabled,
            )

        st.divider()
        st.markdown("### Axes")

        x_axis = st.selectbox(
            "X axis",
            options=list(AXIS_OPTIONS),
            index=list(AXIS_OPTIONS).index("hjd"),
            format_func=AXIS_OPTIONS.get,
        )
        y_axis = st.selectbox(
            "Y axis",
            options=list(AXIS_OPTIONS),
            index=list(AXIS_OPTIONS).index("magnitude"),
            format_func=AXIS_OPTIONS.get,
        )
        only_valid_observations = st.checkbox("Only catflags = 0", value=True)

    return selected_filters, x_axis, y_axis, only_valid_observations


def _render_light_curve(
    *,
    dataframe: pd.DataFrame,
    object_name: str,
    x_axis: str,
    y_axis: str,
) -> None:
    st.caption(f"{len(dataframe):,} observation(s)")

    figure = px.scatter(
        dataframe,
        x=x_axis,
        y=y_axis,
        color="filter",
        color_discrete_map={
            FILTER_LABELS["g"]: FILTER_COLORS["g"],
            FILTER_LABELS["r"]: FILTER_COLORS["r"],
            FILTER_LABELS["i"]: FILTER_COLORS["i"],
        },
        error_y="magnitude_error" if y_axis == "magnitude" else None,
        hover_data=[
            "source_filename",
            "filter",
            "catalog_flags",
            "oid",
            "exposure_id",
        ],
        title=f"{object_name} light curve",
    )
    if y_axis == "magnitude":
        figure.update_yaxes(autorange="reversed")

    figure.update_xaxes(title=AXIS_OPTIONS[x_axis])
    figure.update_yaxes(title=AXIS_OPTIONS[y_axis])
    figure.update_layout(
        height=560,
        legend_title_text="Filter",
        margin={"l": 30, "r": 30, "t": 55, "b": 25},
    )

    st.plotly_chart(figure, use_container_width=True)

    with st.expander(f"Data preview · {object_name}"):
        st.dataframe(dataframe.head(300), use_container_width=True, height=180)


def _prepare_dataframe_for_plot(dataframe: pd.DataFrame) -> pd.DataFrame:
    prepared = dataframe.copy()
    raw_filter_column = _resolve_filter_column(prepared)
    prepared["filter"] = prepared[raw_filter_column].map(
        lambda filter_code: FILTER_LABELS.get(_normalize_filter_code(filter_code)),
    )
    redundant_filter_columns = [
        column
        for column in [
            "series_filter_code",
            "observation_filter_code",
            "normalized_filter",
            "filter_label",
        ]
        if column in prepared.columns
    ]
    prepared = prepared.drop(columns=redundant_filter_columns)
    return prepared[prepared["filter"].notna()]


def _resolve_filter_column(dataframe: pd.DataFrame) -> str:
    for column in ["filter", "series_filter_code", "observation_filter_code"]:
        if column in dataframe.columns:
            return column
    raise KeyError("No filter column found in light-curve data")


def _normalize_filter_code(filter_code: str) -> str:
    if filter_code in {"g", "zg"}:
        return "g"
    if filter_code in {"r", "zr"}:
        return "r"
    if filter_code in {"i", "zi"}:
        return "i"
    return filter_code


def _selected_filters_for_object(*, object_id: int, available_filters: list[str]) -> list[str]:
    state_key = f"selected_filters_{object_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = available_filters.copy()

    return [
        filter_code
        for filter_code in st.session_state[state_key]
        if filter_code in available_filters
    ]


def _toggle_filter(
    *,
    object_id: int,
    filter_code: str,
    selected_filters: list[str],
) -> list[str]:
    updated_filters = selected_filters.copy()
    if filter_code in updated_filters:
        updated_filters.remove(filter_code)
    else:
        updated_filters.append(filter_code)

    state_key = f"selected_filters_{object_id}"
    st.session_state[state_key] = updated_filters
    return updated_filters


def _render_filter_button(
    *,
    object_id: int,
    filter_code: str,
    selected_filters: list[str],
    selected: bool,
    disabled: bool,
) -> list[str]:
    label = FILTER_LABELS[filter_code]
    state = "on" if selected else "off"

    with st.container(key=f"filter_{filter_code}_{state}_{object_id}"):
        st.button(
            label,
            key=f"filter_button_{object_id}_{filter_code}",
            disabled=disabled,
            on_click=_toggle_filter_in_session,
            args=(object_id, filter_code),
            use_container_width=True,
        )
    return selected_filters


def _toggle_filter_in_session(object_id: int, filter_code: str) -> None:
    state_key = f"selected_filters_{object_id}"
    selected_filters = st.session_state.get(state_key, [])
    _toggle_filter(
        object_id=object_id,
        filter_code=filter_code,
        selected_filters=selected_filters,
    )


def _render_filter_chips(available_filters: tuple[str, ...]) -> str:
    if not available_filters:
        return '<span class="filter-chip muted">No filters</span>'

    chips = []
    for filter_code in ["g", "r", "i"]:
        if filter_code not in available_filters:
            continue
        chips.append(
            f'<span class="filter-chip" style="--filter-color: {FILTER_COLORS[filter_code]}">'
            f"{filter_code.upper()}</span>",
        )
    return '<div class="filter-chip-row">' + "".join(chips) + "</div>"


def _available_filters_from_summary(
    astronomical_object: AstronomicalObjectSummary,
) -> tuple[str, ...]:
    available_filters = getattr(astronomical_object, "available_filters", ())
    if available_filters:
        return available_filters
    return tuple(_load_available_filters(astronomical_object.id))


@st.cache_data(show_spinner="Loading objects", ttl=10)
def _load_ztf_objects() -> list[AstronomicalObjectSummary]:
    with session_scope() as session:
        return LightCurveReadRepository(session).list_ztf_objects()


@st.cache_data(show_spinner=False, ttl=10)
def _load_object_name(object_id: int) -> str | None:
    with session_scope() as session:
        return LightCurveReadRepository(session).get_object_name(object_id)


@st.cache_data(show_spinner=False, ttl=10)
def _load_available_filters(object_id: int) -> list[str]:
    with session_scope() as session:
        return LightCurveReadRepository(session).list_available_filters(object_id)


@st.cache_data(show_spinner="Loading observations", ttl=10)
def _load_light_curve(
    *,
    object_id: int,
    selected_filters: list[str],
    only_valid_observations: bool,
) -> pd.DataFrame:
    with session_scope() as session:
        return LightCurveReadRepository(session).load_light_curve(
            object_id=object_id,
            selected_filters=selected_filters,
            only_valid_observations=only_valid_observations,
        )


def _inject_style() -> None:
    stylesheet = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{stylesheet}</style>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
