#
# a script that generates raw data and returns various measures in .csv files for all weapons,
# using either AP or FMJ vs. all protection grades according to https://ghosts-of-tabor.fandom.com/wiki/Ballistics
#
# written by ashphalt
#
import random
import statistics
import pen_stats # import own pen_stats.py; contains pen chance, damage etc
import csv
import itertools


# runs_per_weapon : sample size to simulate for each weapon
# column_headers : list of all weapons in input file
calibers = pen_stats.calibers
weapons = pen_stats.weapons
runs_per_weapon = 1000
selected_round_type = "_" + (input("ap/fmj?").lower())
random.seed(1890740189734981734)

column_headers = [weapon for weapon in weapons]
summary_stats_list = [[] for i in range(0, len(weapons))]
stats_column_headers = ["Weapon", "Minimum", "Q1", "Q3", "Maximum", "Median", "IQR"]
median_stats_list = [[i] for i in weapons] # init with 40 rows headed by weapon
median_column_headers = ["Weapon", "pg2", "pg3", "pg4", "pg5", "pg6"]
count_column_headers = column_headers.copy()
for a in range(0, len(column_headers)):  # create bin headers for columns
    count_column_headers.insert(a * 2, count_column_headers[a * 2] + "_bins")


# generate_samples()
#
# find the selected caliber, and the damage a given weapon deals
# run 'runs_per_weapon' simulated kills accounting for pen chance, dmg reduction from armour
# populate ttk_list vertically
#
def generate_samples(selected_protection):
    for weapon in weapons:
        base_caliber = (weapons[weapon]["caliber"]) + selected_round_type  # ap/fmj
        selected_caliber = calibers[base_caliber]
        time_per_round = round((1 / ((weapons[weapon]["rpm"]) / 60)) * 1000)  # conversion to seconds per round
        dmg_per_round = (weapons[weapon][base_caliber])
        invulnerable = selected_caliber[selected_protection]["pen_chance"] == 0.0 or \
            selected_caliber[selected_protection]["dmg_reduction"] == 1.0

        sim_runs = runs_per_weapon
        current_row_index = 0
        while sim_runs > 0:
            rounds_to_kill = 0
            health = 100

            while health > 0:
                rounds_to_kill += 1  # simulate a failed pen
                if invulnerable:
                    break
                elif random.random() <= selected_caliber[selected_protection]["pen_chance"]:
                    health -= dmg_per_round * (1.0 - selected_caliber[selected_protection]["dmg_reduction"])

            if invulnerable:
                ttk_list[current_row_index].append(0)  # 0 value must be deleted in sheet
            else:
                ttk_list[current_row_index].append((rounds_to_kill - 1) * time_per_round)

            current_row_index += 1
            sim_runs -= 1


#
# for all weapons against all PGs tabulate medians, summary statistics, raw data, counts in csvs,
#
current_row_index = 0
for prot_grade in median_column_headers[1:]:  # for every prot grade
    print("----------------")
    print(prot_grade)

    ttk_list = [[] for i in range(runs_per_weapon)]
    generate_samples(prot_grade)
    vertical_ttk_list = list(itertools.zip_longest(*ttk_list))

    #
    # ongoing tabulation of median TTK for all prot grades
    #
    current_row_index = 0
    for x in median_stats_list:
        x.append(statistics.median(vertical_ttk_list[current_row_index]))
        current_row_index += 1

    #
    # tabulate counts of unique bin values into table
    #
    counts_row_header_list = []  # each bin in the histogram
    counts_list = []  # the counts for each item for above

    current_row_index = 0
    for column in vertical_ttk_list:  # each 'list of TTKs'
        sorted_uniques = list(set(column))
        sorted_uniques.sort()
        counts_list.append([0 for i in range(len(sorted_uniques))])  # create new column w/ length of uniques
        current_counts_list_index = 0  # keep track of location in counts_list

        for count_bin in sorted_uniques:  # each 'bin' in the list, count em up
            counts_list[current_row_index][current_counts_list_index] = column.count(count_bin)
            current_counts_list_index += 1

        current_row_index += 1
        counts_row_header_list.append(sorted_uniques)

    export_counts_list = []
    for column in range(0, len(column_headers)):  # append bins and counts into order
        export_counts_list.append(counts_row_header_list[column])
        export_counts_list.append(counts_list[column])
    export_counts_list = itertools.zip_longest(*export_counts_list)

    with open(f'counts_{selected_round_type}_{prot_grade}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(count_column_headers)
        writer.writerows(export_counts_list)

    #
    # tabulate summary statistics
    #
    current_row_index = 0
    for y in summary_stats_list:
        quartiles = statistics.quantiles(vertical_ttk_list[current_row_index])
        y.append(column_headers[current_row_index])
        y.append(min(vertical_ttk_list[current_row_index]))
        y.append(quartiles[0])
        y.append(quartiles[2])
        y.append(max(vertical_ttk_list[current_row_index]))
        y.append(statistics.median(vertical_ttk_list[current_row_index]))
        y.append(quartiles[2] - quartiles[0])
        current_row_index += 1


    #
    # tabulate raw data for debug
    #
    with open(f'raw_output_{selected_round_type}_{prot_grade}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(column_headers)
        writer.writerows(ttk_list)


with open(f'summary_stats_{selected_round_type}_all.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(stats_column_headers)
    writer.writerows(summary_stats_list)

with open(f'all_medians{selected_round_type}.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(median_column_headers)
    writer.writerows(median_stats_list)

print("Completed!")
