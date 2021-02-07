import json
import math
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('seaborn-darkgrid')

with open("allsides.json") as f:
    data = json.load(f)


# Which ratings for outlets does the community absolutely agree on?
abs_agree = [d for d in data if d['agreeance_text'] == "absolutely agrees"]

print(f"{'Outlet':<30} {'Bias':<20}")
print("-" * 40)
for d in abs_agree:
    print(f"{d['name']:<30} {d['bias']:<20}")


# Which ratings for outlets does the community absolutely disagree on?
with open("allsides.json") as f:
    df = pd.read_json(f)

df.set_index('name', inplace=True)

df_str_dis = df[df['agreeance_text'] == 'strongly disagrees']
print("No strongly disagrees since shape =", df_str_dis.shape)

#
df['total_votes'] = df['agree'] + df['disagree']
df.sort_values('total_votes', ascending=False, inplace=True)

print(df.head(10))

# Visualising the 25 most voted sites
df_head = df.head(25).copy()

fig, ax = plt.subplots(figsize=(20, 10))
ax.bar(df_head.index, df_head['agree'], color='#5DAF83')
ax.bar(df_head.index, df_head['disagree'], bottom=df_head['agree'], color='#AF3B3B')

ax.set_ylabel = 'Total feedback'

plt.yticks(fontsize='x-large')
plt.xticks(rotation=60, ha='right', fontsize='x-large', rotation_mode='anchor')

plt.legend(['Agree', 'Disagree'], fontsize='xx-large')
plt.title('AllSides Bias Rating vs. Community Feedback', fontsize='xx-large')
plt.show()

# Make a subplot for each bias and plot the respective new sources
df3 = df.copy()
biases = df3['bias'].unique()

fig = plt.figure(figsize=(15, 15))
for i, bias in enumerate(biases):
    # Get top 10 news sources for this bias and sort alphabetically
    temp_df = df3[df['bias'] == bias].iloc[:10]
    temp_df.sort_index(inplace=True)

    # Get max votes
    max_votes = temp_df['total_votes'].max()

    # Add a new subplot in the correct position
    ax = fig.add_subplot(math.ceil(len(biases) / 2), 2, i + 1)

    # Create the stacked bars
    ax.bar(temp_df.index, temp_df['agree'], color='#5DAF83')
    ax.bar(temp_df.index, temp_df['disagree'], bottom=temp_df['agree'], color='#AF3B3B')

    # Place text for the ratio on top of each bar
    for x, y, ratio in zip(ax.get_xticks(), temp_df['total_votes'], temp_df['agree_ratio']):
        ax.text(x, y + (0.02 * max_votes), f"{ratio:.2f}", ha='center')

    ax.set_ylabel('Total feedback')
    ax.set_title(bias.title())

    # Make y limit larger to compensate for text on bars
    ax.set_ylim(0, max_votes + (0.12 * max_votes))

    # Rotate tick labels so they don't overlap
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

plt.tight_layout(w_pad=3.0, h_pad=1.0)
plt.show()

