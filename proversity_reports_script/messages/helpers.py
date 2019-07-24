"""
Helper module with utilities to generate the content of a message.
"""
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')
import seaborn as sns
sns.set()


def generate_graph(**kwargs):
    """
    Helper method to generate a graph from its subplots.
    """

    if not kwargs.get("subplots"):
        return None

    try:
        script_dir = os.path.dirname(__file__)
        rel_path = "images/output.png"
        fig, axes = plt.subplots(
            nrows=1,
            ncols=len(kwargs["subplots"]),
            figsize=(10.0, 5.0)
        )
        fig.subplots_adjust(hspace=0.5)

        for idx, subplot in enumerate(kwargs["subplots"]):
            sns.barplot(
                x=subplot["x"],
                y=subplot["y"],
                data=subplot["data"],
                ax=axes[idx],
                palette=subplot["palette"],
            )
            axes[idx].set_xlabel('')
            axes[idx].title.set_text(subplot["title"])
            axes[idx].set_ylabel(subplot["ylabel"])

        fig.tight_layout()
        fig.savefig(os.path.join(script_dir, rel_path))
    except Exception:
        return None
    else:
        return "Completed"


def generate_student_subplots(user_record, graph_confs):
    """
    Generate a subplots data for the main graph.
    """

    subplots_data = []

    for graph in graph_confs:
        try:
            subplots_data.append({
                "x": "metric_category",
                "y": graph["metric"],
                "data": pd.DataFrame({
                    graph["metric"]: [
                        graph["passing_score"],
                        user_record[graph["metric"]]
                    ],
                    "metric_category": ["Target", "You"]
                }),
                "ylabel": graph["ylabel"],
                "title": graph["graph_title"],
                "palette": "Blues_d",
            })
        except Exception as identifier:
            raise identifier

    return subplots_data
