import seaborn as sns
import matplotlib.pyplot as plt

def plot_rates(diagnosis_ci,ax=None):
    #diagnosis_ci["diagnosis"]=diagnosis_ci["diagnosis_labels"]
    ax = sns.pointplot(
        data=diagnosis_ci,
        y="diagnosis_labels",
        x="rate",
        hue="sex",
        ax=ax,
        palette={
            "Female": "black",
            "Male": "red",
        },
        linestyle="None",
        markersize=3,
        dodge=.4,
    )
    ax.set_xlabel("Readmission rate")
    ax.set_ylabel("")
    ax.set_xlim(0, .6)
    diagnoses = diagnosis_ci["diagnosis_labels"].unique()

    y_lookup = {
        diagnosis: i
        for i, diagnosis in enumerate(diagnoses)
    }

    offsets = {
        "Female": -0.2,
        "Male": 0.2,    
    }

    for sex, colour in {
        "Female": "black",
        "Male": "red",
    }.items():

        subset = diagnosis_ci[
            diagnosis_ci["sex"] == sex
        ]

        y_pos = [
            y_lookup[d] + offsets[sex]
            for d in subset["diagnosis_labels"]
        ]

        ax.errorbar(
            y=y_pos,
            x=subset["rate"],
            xerr=[
                subset["rate"] - subset["ci_lower"],
                subset["ci_upper"] - subset["rate"]
            ],
            fmt="none",
            color=colour,
            capsize=4,
        )
        ax.legend(
            title=None,
            frameon=False,
            #bbox_to_anchor=(0.9, 1),
            loc="upper right"
        )
    plt.tight_layout()
    return ax
