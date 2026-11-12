# Brexit 2016: what explains the Leave vote
# A Streamlit version of the Tableau dashboard "What explains Leave vote".
#
# Run it with:   streamlit run app.py
# Data needed:   data/gb_areas_clean.csv and data/gb_areas_boundaries.geojson
#
# All the numbers are computed in brexit_data.py with the same formulas as
# Tableau and notebook 02, so the app and the notebooks always agree.

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import brexit_data as bd

st.set_page_config(
    page_title="Brexit 2016 · What explains the Leave vote",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Colours and fonts
# Blue = Remain side, red = Leave side, light grey = 50/50.
# ---------------------------------------------------------------------------
REMAIN, LEAVE = "#2a78d6", "#e34948"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, NEUTRAL = "#e1e0d9", "#c3c2b7", "#f0efec"
FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
DIVERGING = [[0.0, "#184f95"], [0.25, "#86b6ef"], [0.5, NEUTRAL], [0.75, "#f09594"], [1.0, "#b52f2f"]]

st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1440px; }}
      .eyebrow {{ color: {MUTED}; font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; }}
      .hero h1 {{ font-size: 2.3rem; line-height: 1.15; margin: .2rem 0 .4rem 0; color: {INK}; font-weight: 700; }}
      .hero p {{ color: {INK2}; font-size: 1.05rem; max-width: 60rem; margin: 0; }}
      .kpi {{ background: #fcfcfb; border: 1px solid rgba(11,11,11,.08); border-radius: 14px;
              padding: 16px 18px 14px; height: 100%; }}
      .kpi .label {{ color: {INK2}; font-size: .85rem; font-weight: 600; }}
      .kpi .value {{ color: {INK}; font-size: 2.1rem; font-weight: 700; line-height: 1.15; margin-top: 2px; }}
      .kpi .note {{ color: {MUTED}; font-size: .8rem; margin-top: 4px; }}
      .split {{ position: relative; display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 10px; gap: 2px; }}
      .split .tick {{ position: absolute; left: 50%; top: -3px; bottom: -3px; width: 2px; background: {INK}; }}
      .chart-title {{ font-size: 1.08rem; font-weight: 650; color: {INK}; margin: .2rem 0 0 0; }}
      .chart-sub {{ font-size: .88rem; color: {INK2}; margin: .1rem 0 .4rem 0; }}
      .source {{ color: {MUTED}; font-size: .8rem; border-top: 1px solid {GRID}; padding-top: .8rem; margin-top: 2rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data (loaded once, then kept in memory)
# ---------------------------------------------------------------------------
@st.cache_data
def get_data():
    areas = bd.load_areas()
    geo, points = bd.load_boundaries()
    return areas, geo, points.set_index("code")


areas, geo, points = get_data()
GB = bd.kpis(areas)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def style(fig, height=420):
    """Same clean look on every chart: thin grid, no box, readable hover."""
    fig.update_layout(
        height=height,
        font=dict(family=FONT, size=13, color=INK2),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=8, b=8),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, size=13, color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title=None),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED))
    return fig


def title(text, sub=None):
    st.markdown(f'<p class="chart-title">{text}</p>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<p class="chart-sub">{sub}</p>', unsafe_allow_html=True)


def kpi(label, value, note="", leave_share=None):
    bar = ""
    if leave_share is not None:  # small Leave / Remain bar with a 50% tick
        bar = (f'<div class="split"><div style="width:{leave_share:.1f}%;background:{LEAVE}"></div>'
               f'<div style="flex:1;background:{REMAIN}"></div><div class="tick"></div></div>')
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>'
                f'{bar}<div class="note">{note}</div></div>', unsafe_allow_html=True)


def choropleth(df, value_col, value_name, zmin, zmax, hover_cols, callouts=()):
    """Map of the areas in df. Areas outside the selection stay in light grey."""
    fig = go.Figure()

    hidden = areas[~areas["code"].isin(df["code"])]
    if len(hidden):
        fig.add_trace(go.Choropleth(
            geojson=geo, featureidkey="properties.code", locations=hidden["code"], z=np.zeros(len(hidden)),
            colorscale=[[0, "#ebeae5"], [1, "#ebeae5"]], showscale=False, hoverinfo="skip",
            marker=dict(line=dict(color="white", width=0.3)),
        ))

    # Hover text: area name, region, then the chosen columns with their units
    lines = [f"<b>%{{customdata[0]}}</b><br><span style='color:{MUTED}'>%{{customdata[1]}}</span><br>"]
    for i, (label, _col, fmt) in enumerate(hover_cols, start=2):
        lines.append(f"{label}: %{{customdata[{i}]:{fmt}}}<br>")
    # object dtype keeps numbers as numbers (column_stack would turn them into text)
    custom = df[["area", "region"] + [c for _l, c, _f in hover_cols]].to_numpy(dtype=object)

    fig.add_trace(go.Choropleth(
        geojson=geo, featureidkey="properties.code", locations=df["code"], z=df[value_col],
        zmin=zmin, zmax=zmax, colorscale=DIVERGING, customdata=custom,
        hovertemplate="".join(lines) + "<extra></extra>",
        marker=dict(line=dict(color="white", width=0.3)),
        colorbar=dict(orientation="h", x=0.5, xanchor="center", y=-0.02, yanchor="top", len=0.7, thickness=10,
                      title=dict(text=value_name, side="top", font=dict(size=12, color=INK2)),
                      tickfont=dict(color=MUTED, size=11), outlinewidth=0),
    ))

    # Direct labels on a few areas (highest, lowest, the one searched)
    if callouts:
        c = df[df["code"].isin(callouts)].join(points, on="code")
        fig.add_trace(go.Scattergeo(
            lon=c["lon"], lat=c["lat"], mode="markers+text", hoverinfo="skip",
            text=[f"<b>{a}</b> {v:.1f}%" for a, v in zip(c["area"], c[value_col])],
            textposition="middle right", textfont=dict(family=FONT, size=12, color=INK),
            marker=dict(size=7, color="white", line=dict(color=INK, width=2)),
        ))

    # Zoom on the selected areas
    p = points.loc[df["code"]]
    pad_lon = max(0.6, (p["lon"].max() - p["lon"].min()) * 0.08)
    pad_lat = max(0.4, (p["lat"].max() - p["lat"].min()) * 0.05)
    fig.update_geos(
        visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)",
        lonaxis_range=[p["lon"].min() - pad_lon, p["lon"].max() + pad_lon * 2.5],
        lataxis_range=[p["lat"].min() - pad_lat, p["lat"].max() + pad_lat],
    )
    style(fig, height=660)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=40), showlegend=False, dragmode=False)
    return fig


def band_label(b, low, high, col):
    """X-axis label for one group of areas, with the range of values it covers."""
    names = {1: "Lowest 20%", 2: "20-40%", 3: "40-60%", 4: "60-80%", 5: "Highest 20%"}
    return f"{names[b]}<br><span style='color:{MUTED};font-size:11px'>" \
           f"{bd.fmt_measure(col, low)} – {bd.fmt_measure(col, high)}</span>"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">EU referendum · 23 June 2016 · 380 areas of Great Britain</div>
      <h1>What explains the Leave vote</h1>
      <p>Education explains the Leave vote better than anything else: the fewer graduates an area has,
      the more it voted Leave.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# ---------------------------------------------------------------------------
# Filters in one row, above the charts (same filters as the Tableau map)
# ---------------------------------------------------------------------------
f1, f2, f3, f4 = st.columns([2.2, 1.8, 1.8, 1.8])
regions = f1.multiselect("Region", sorted(areas["region"].unique()), placeholder="All regions")
# Pay range in pounds (rounded to £10 so the slider ends are clean numbers)
pay_min = int(np.floor(areas["median_weekly_pay"].min() / 10) * 10)
pay_max = int(np.ceil(areas["median_weekly_pay"].max() / 10) * 10)
pay = f2.slider("Median weekly pay (£)", pay_min, pay_max, (pay_min, pay_max), step=10, format="£%d")
ukip_min, ukip_max = float(np.floor(areas["ukip_2014_pct"].min())), float(np.ceil(areas["ukip_2014_pct"].max()))
ukip = f3.slider("UKIP vote in 2014 (%)", ukip_min, ukip_max, (ukip_min, ukip_max), step=1.0, format="%d%%")
found = f4.selectbox("Search an area", sorted(areas["area"]), index=None, placeholder="Type an area name")

sel = areas.copy()
if regions:
    sel = sel[sel["region"].isin(regions)]
# Isles of Scilly has no pay figure: it stays in unless the pay range is narrowed
pay_all = pay == (pay_min, pay_max)
sel = sel[sel["median_weekly_pay"].between(*pay) | (pay_all & sel["median_weekly_pay"].isna())]
sel = sel[sel["ukip_2014_pct"].between(*ukip)]
filtered = len(sel) < len(areas)

if sel.empty:
    st.warning("No area matches these filters. Widen the pay or UKIP range, or clear the regions.")
    st.stop()

# ---------------------------------------------------------------------------
# Headline figures
# ---------------------------------------------------------------------------
k = {"leave_share": bd.weighted_leave(sel), "areas": len(sel), "leave_areas": int((sel["leave_pct"] > 50).sum()),
     "turnout": 100 * sel["votes_cast"].sum() / sel["electorate"].sum(),
     "graduate_gap": bd.gap(sel, "pct_degree") if len(sel) >= 25 else np.nan}
gb_note = (lambda v: f"Great Britain: {v}") if filtered else (lambda v: "")

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Leave share", f"{k['leave_share']:.1f}%",
        gb_note(f"{GB['leave_share']:.1f}%") or "Share of all valid votes", leave_share=k["leave_share"])
with c2:
    kpi("Areas won by Leave", f"{k['leave_areas']} <span style='font-size:1.1rem;color:{MUTED}'>of {k['areas']}</span>",
        gb_note(f"{GB['leave_areas']} of {GB['areas']}") or f"{100 * k['leave_areas'] / k['areas']:.0f}% of areas above 50% Leave")
with c3:
    g = k["graduate_gap"]
    kpi("Graduate gap", f"{g:+.1f} pts" if not np.isnan(g) else "n/a",
        "Leave share in the 20% of areas with most graduates minus the 20% with fewest")
with c4:
    kpi("Turnout", f"{k['turnout']:.1f}%", gb_note(f"{GB['turnout']:.1f}%") or "Votes cast / electorate")

st.write("")
left, right = st.columns([1.15, 1], gap="large")

# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------
with left:
    view = st.radio("Colour the map by", ["Each area", "Its region"], horizontal=True, label_visibility="collapsed")
    col = "leave_pct" if view == "Each area" else "region_leave_pct"
    top = sel.nlargest(1, "leave_pct")["code"].tolist()
    low = sel.nsmallest(1, "leave_pct")["code"].tolist()
    pick = areas.loc[areas["area"] == found, "code"].tolist() if found else []
    title("Leave share by area",
          "Red = Leave majority, blue = Remain majority. Labels show the highest and lowest areas in the selection.")
    st.plotly_chart(
        choropleth(sel, col, "Leave share (%)", 20, 80,
                   hover_cols=[("Leave", "leave_pct", ".1f"), ("Region Leave", "region_leave_pct", ".1f"),
                               ("Graduates", "pct_degree", ".1f"), ("UKIP 2014", "ukip_2014_pct", ".1f"),
                               ("Weekly pay £", "median_weekly_pay", ",.0f")],
                   callouts=top + low + pick),
        config={"displayModeBar": False, "scrollZoom": False},
    )
    if found and found not in set(sel["area"]):
        st.caption(f"{found} is hidden by the current filters.")
    st.caption("Large rural areas fill much of the map but hold fewer voters.")

# ---------------------------------------------------------------------------
# What goes with the Leave vote
# ---------------------------------------------------------------------------
with right:
    show_all = st.toggle("Show all 10 measures", value=False)
    cols = list(bd.MEASURES) if show_all else bd.TABLEAU_KPIS
    title("What goes with the Leave vote",
          "Leave share in the 20% of areas with the highest value minus the 20% with the lowest, in points")
    if len(sel) < 25:
        st.info("Select at least 25 areas to compare.")
    else:
        gaps = bd.gap_table(sel, cols)
        fig = go.Figure(go.Bar(
            x=gaps["gap"], y=gaps["measure"], orientation="h",
            marker=dict(color=np.where(gaps["gap"] > 0, LEAVE, REMAIN), cornerradius=4),
            text=[f"{v:+.1f}" for v in gaps["gap"]], textposition="outside", cliponaxis=False,
            textfont=dict(color=INK, size=12),
            customdata=np.column_stack([gaps["bottom"], gaps["top"], gaps["r"]]),
            hovertemplate="<b>%{y}</b><br>Lowest 20% of areas: %{customdata[0]:.1f}% Leave"
                          "<br>Highest 20% of areas: %{customdata[1]:.1f}% Leave<br>Gap: %{x:+.1f} pts"
                          "<br>Correlation r = %{customdata[2]:.2f}<extra></extra>",
        ))
        fig.add_vline(x=0, line_color=AXIS, line_width=1)
        lim = gaps["gap"].abs().max() * 1.25
        style(fig, height=70 + 34 * len(gaps))
        fig.update_xaxes(range=[-lim, lim], ticksuffix=" pts", showgrid=True)
        fig.update_yaxes(showgrid=False, tickfont=dict(color=INK, size=13))
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption("UKIP 2014 is a political measure: it predicts Leave but does not explain it through demographics.")

        # --- Leave share from the lowest to the highest areas ---------------
        measure = st.selectbox("Measure", list(bd.MEASURES), format_func=bd.MEASURES.get, index=0)
        b = bd.band_shares(sel, measure).dropna(subset=["leave"])
        first, last = b.iloc[0], b.iloc[-1]
        title(f"{bd.MEASURES[measure]}: Leave goes from {first['leave']:.0f}% to {last['leave']:.0f}%",
              f"Areas sorted by {bd.MEASURES[measure].lower()}, from the lowest to the highest "
              f"({last['leave'] - first['leave']:+.1f}-point gap)")
        colour = LEAVE if last["leave"] > first["leave"] else REMAIN
        fig = go.Figure(go.Scatter(
            x=[band_label(r.band, r.low, r.high, measure) for r in b.itertuples()], y=b["leave"],
            mode="lines+markers+text", line=dict(color=colour, width=2),
            marker=dict(size=10, color=colour, line=dict(color="white", width=2)),
            text=[f"{v:.1f}%" for v in b["leave"]], textposition="top center",
            textfont=dict(color=INK, size=12), customdata=b["areas"],
            hovertemplate="%{x}<br>Leave: %{y:.1f}%<br>%{customdata} areas<extra></extra>",
        ))
        fig.add_hline(y=50, line_dash="dot", line_color=MUTED, annotation_text="50%",
                      annotation_position="right", annotation_font_color=MUTED)
        style(fig, height=330)
        fig.update_yaxes(range=[min(30, b["leave"].min() - 5), max(70, b["leave"].max() + 6)], ticksuffix="%")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
st.markdown(
    '<div class="source">Sources: Electoral Commission (2016 results), 2011 Census, ONS, European Parliament '
    "elections 2014. 380 counting areas of Great Britain (Northern Ireland and Gibraltar excluded). Boundaries: "
    "Ordnance Survey and ONS data © Crown copyright 2014, via UK-GeoJSON by Martin Chorley (CC BY 4.0). "
    "Results describe areas, not individual voters.</div>",
    unsafe_allow_html=True,
)
