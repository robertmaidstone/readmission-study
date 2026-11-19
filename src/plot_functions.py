import seaborn as sns
import matplotlib.pyplot as plt

def plot_rates(diagnosis_ci):
    ax = sns.pointplot(
        data=diagnosis_ci,
        x="diagnosis",
        y="rate",
        hue="sex",
        linestyle="None",
    dodge=.2,
    )
    ax.set_ylabel("30-day unplanned readmission rate")
    ax.set_xlabel("Index admission diagnosis")
    ax.set_ylim(0, .7)
    diagnoses = diagnosis_ci["diagnosis"].unique()

    x_lookup = {
        diagnosis: i
        for i, diagnosis in enumerate(diagnoses)
    }

    offsets = {
        "Female": -0.1,
        "Male": 0.1,    
    }

    for sex, colour in {
        "Female": "blue",
        "Male": "orange",
    }.items():

        subset = diagnosis_ci[
            diagnosis_ci["sex"] == sex
        ]

        x_pos = [
            x_lookup[d] + offsets[sex]
            for d in subset["diagnosis"]
        ]

        ax.errorbar(
            x=x_pos,
            y=subset["rate"],
            yerr=[
                subset["rate"] - subset["ci_lower"],
                subset["ci_upper"] - subset["rate"]
            ],
            fmt="none",
            color=colour,
            capsize=4,
        )
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()