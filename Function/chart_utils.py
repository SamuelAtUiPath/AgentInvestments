import os
from math import cos, radians, sin

import matplotlib
import pandas as pd

from uipath.tracing import traced


matplotlib.use("Agg")

PAPER_BACKGROUND = "#1f1f1f"
CHART_BACKGROUND = "#1f1f1f"
FONT_COLOR = "#f2f2f2"
TYPE_COLORS: dict[str, str] = {}
DEFAULT_PALETTE = [
    "#f28490",
    "#3a86ff",
    "#ffb703",
    "#9b5de5",
    "#43aa8b",
    "#8ecae6",
    "#fb8500",
    "#90be6d",
    "#577590",
    "#f94144",
    "#277da1",
    "#bc6c25",
]


def format_brl(value) -> str:
    if pd.isna(value):
        return "R$ 0,00"

    value = float(value)
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def make_color_sequence(labels: list[str], type_colors: dict[str, str] | None = None) -> list[str]:
    color_map = type_colors or TYPE_COLORS
    return [
        color_map.get(label, DEFAULT_PALETTE[index % len(DEFAULT_PALETTE)])
        for index, label in enumerate(labels)
    ]


def _portfolio_title(category: str | None) -> str:
    category = (category or "").strip()
    if category:
        return f"Composi\u00e7\u00e3o de {category}"
    return "Composi\u00e7\u00e3o do Portf\u00f3lio"


def _format_percent(value: float, total: float) -> str:
    if total <= 0:
        return "0%"
    return f"{(value / total * 100):.3g}%"


def _base_chart(title: str):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 7), dpi=100)
    fig.patch.set_facecolor(PAPER_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(
        0.025,
        0.965,
        title,
        color=FONT_COLOR,
        fontsize=20,
        fontfamily="Arial",
        ha="left",
        va="top",
    )
    return fig, ax


def _draw_center_text(ax, center_text: str):
    lines = [line for line in (center_text or "").split("\n") if line]
    if not lines:
        return

    if len(lines) == 1:
        ax.text(
            0,
            0,
            lines[0],
            color=FONT_COLOR,
            fontsize=24,
            fontfamily="Arial",
            ha="center",
            va="center",
        )
        return

    ax.text(
        0,
        0.035,
        lines[0],
        color=FONT_COLOR,
        fontsize=24,
        fontfamily="Arial",
        fontweight="bold",
        ha="center",
        va="center",
    )
    ax.text(
        0,
        -0.085,
        lines[1],
        color=FONT_COLOR,
        fontsize=24,
        fontfamily="Arial",
        ha="center",
        va="center",
    )


def _placeholder_figure(title: str, center_text: str):
    fig, ax = _base_chart(title)
    _draw_center_text(ax, center_text or "Sem dados dispon\u00edveis")
    return fig


def build_donut_chart(
    df_plot: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    center_text: str | None = None,
    colors: list[str] | None = None,
):
    labels = df_plot[label_col].astype(str).tolist()
    values = df_plot[value_col].astype(float).tolist()

    if colors is None:
        colors = make_color_sequence(labels)

    fig, ax = _base_chart(title)
    total = sum(values)
    wedges, _texts = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        explode=[0.025] * len(labels),
        radius=1.0,
        wedgeprops=dict(width=0.28, edgecolor=CHART_BACKGROUND, linewidth=7),
    )

    for wedge, label, value in zip(wedges, labels, values):
        angle = (wedge.theta1 + wedge.theta2) / 2
        x = 1.22 * cos(radians(angle))
        y = 1.22 * sin(radians(angle))
        horizontal_alignment = "left" if x >= 0 else "right"
        ax.text(
            x,
            y,
            f"{_format_percent(value, total)}\n{label}\n{format_brl(value)}",
            color=FONT_COLOR,
            fontsize=12,
            fontfamily="Arial",
            ha=horizontal_alignment,
            va="center",
        )

    _draw_center_text(ax, center_text or "")
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.2, 1.2)
    return fig


@traced(name="creating donut chart png")
def create_donut_chart_png(
    df: pd.DataFrame,
    category: str = "",
    label_col: str = "Name",
    value_col: str = "Value",
    output_path: str = "output.png",
) -> str:
    image_path = os.path.abspath(output_path)
    image_dir = os.path.dirname(image_path)
    if image_dir:
        os.makedirs(image_dir, exist_ok=True)

    title = _portfolio_title(category)
    category_text = (category or "").strip()

    df_plot = df.copy()
    if label_col not in df_plot.columns or value_col not in df_plot.columns:
        center_text = category_text if category_text else ""
        fig = _placeholder_figure(title, center_text)
        fig.savefig(image_path, format="png", dpi=100, facecolor=fig.get_facecolor())
        matplotlib.pyplot.close(fig)
        return image_path

    df_plot[value_col] = pd.to_numeric(df_plot[value_col], errors="coerce")
    df_plot = df_plot.dropna(subset=[label_col, value_col])
    df_plot = df_plot[df_plot[value_col] > 0]
    df_plot = (
        df_plot.groupby(label_col, as_index=False, sort=False)[value_col]
        .sum()
    )

    total = df_plot[value_col].sum()
    center_lines = []
    if category_text:
        center_lines.append(category_text)
    if total > 0:
        center_lines.append(format_brl(total))
    center_text = "\n".join(center_lines)

    if df_plot.empty or total <= 0:
        fig = _placeholder_figure(title, center_text or "Sem dados dispon\u00edveis")
    else:
        fig = build_donut_chart(
            df_plot=df_plot,
            label_col=label_col,
            value_col=value_col,
            title=title,
            center_text=center_text,
        )

    fig.savefig(image_path, format="png", dpi=100, facecolor=fig.get_facecolor())
    matplotlib.pyplot.close(fig)
    return image_path


@traced(name="creating dataframe png")
def create_dataframe_png(
    df: pd.DataFrame,
    output_path: str = "output.png",
) -> str:
    import matplotlib.pyplot as plt

    image_path = os.path.abspath(output_path)
    image_dir = os.path.dirname(image_path)
    if image_dir:
        os.makedirs(image_dir, exist_ok=True)

    display_df = df.copy()
    if display_df.empty:
        display_df = pd.DataFrame([["No data available"]], columns=["Message"])

    display_df = display_df.astype(str)

    row_count = len(display_df.index)
    column_count = len(display_df.columns)
    figure_width = max(6, column_count * 2)
    figure_height = max(2, (row_count + 1) * 0.5)

    fig, ax = plt.subplots(figsize=(figure_width, figure_height))
    ax.axis("off")

    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.4)

    for (row, _column), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#D9EAF7")
        else:
            cell.set_facecolor("#FFFFFF")

    fig.tight_layout()
    fig.savefig(image_path, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    return image_path
