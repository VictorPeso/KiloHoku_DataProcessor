"""Streamlit app for database-backed light-curve visualization."""

import pandas as pd
import plotly.express as px
import streamlit as st

from data_processor.config.settings import get_settings
from data_processor.infrastructure.database.repositories.light_curve_repository import (
    AstronomicalObjectSummary,
    LightCurveReadRepository,
)
from data_processor.infrastructure.database.session import session_scope


def main() -> None:
    st.set_page_config(page_title="Light Curve Viewer", layout="wide")
    st.title("Light Curve Viewer")

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
        columns = st.columns([4, 2, 2, 2])
        columns[0].markdown(f"**{astronomical_object.source_name}**")
        columns[1].write(f"Series: {astronomical_object.series_count}")
        columns[2].write(f"Obs: {astronomical_object.observation_count:,}")
        if columns[3].button("Open", key=f"open-{astronomical_object.id}"):
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

    header_columns = st.columns([4, 1])
    header_columns[0].subheader(object_name)
    if header_columns[1].button("Back"):
        st.session_state.selected_object_id = None
        st.rerun()

    available_filters = _load_available_filters(object_id)
    if not available_filters:
        st.warning("This object has no photometric series with filters g, r, or i.")
        return

    selected_filters = st.multiselect(
        "Curves",
        options=["g", "r", "i"],
        default=available_filters,
        disabled=False,
    )
    selected_filters = [
        filter_code for filter_code in selected_filters if filter_code in available_filters
    ]

    only_valid_observations = st.checkbox("Only catflags = 0", value=True)
    time_axis = st.selectbox("Time axis", options=["hjd", "mjd"], index=0)

    if not selected_filters:
        st.info("Select at least one curve to display.")
        return

    try:
        dataframe = _load_light_curve(
            object_id=object_id,
            selected_filters=selected_filters,
            only_valid_observations=only_valid_observations,
        )
    except Exception as exc:
        st.error(f"Could not load light curve data from PostgreSQL: {exc}")
        return

    if dataframe.empty:
        st.warning("No observations match the selected filters.")
        return

    if time_axis not in dataframe.columns or dataframe[time_axis].isna().all():
        st.error(f"No usable values found for `{time_axis}`.")
        return

    _render_light_curve(dataframe=dataframe, time_axis=time_axis)


def _render_light_curve(*, dataframe: pd.DataFrame, time_axis: str) -> None:
    st.caption(f"{len(dataframe):,} observation(s)")

    figure = px.scatter(
        dataframe,
        x=time_axis,
        y="magnitude",
        color="series_filter_code",
        error_y="magnitude_error",
        hover_data=[
            "source_filename",
            "observation_filter_code",
            "catalog_flags",
            "oid",
            "exposure_id",
        ],
        title="Light curve",
    )
    figure.update_yaxes(autorange="reversed", title="Magnitude")
    figure.update_xaxes(title=time_axis.upper())
    figure.update_layout(height=720, legend_title_text="Filter")

    st.plotly_chart(figure, use_container_width=True)

    with st.expander("Data preview"):
        st.dataframe(dataframe.head(500), use_container_width=True)


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


if __name__ == "__main__":
    main()
