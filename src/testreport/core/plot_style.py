from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt


def apply_default_rcparams() -> None:
    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.labelsize": 14,
            "axes.titlesize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 12,
        }
    )


def place_legend_below(ax, *, ncol: int = 4, y: float = -0.30) -> None:
    """Place legend centered below plot, far enough down to clear x tick labels."""
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return

    ncol = max(1, min(int(ncol), len(labels)))
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, y),
        ncol=ncol,
        framealpha=0.9,
    )


def finalize_and_save(fig, out_path: str | Path, *, dpi: int = 150) -> Path:
    """
    Leave extra bottom margin for the below-plot legend, then save.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # More bottom space than before so legend clears x-axis text
    # fig.tight_layout(rect=(0.1, 0.3, 1.0, 1.0))
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path
