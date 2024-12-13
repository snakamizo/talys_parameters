import os
from config import LATEX_DOCUMENT_FILENAME


def generate_latex_document(output_directory):
    latex_content = (
        "\\documentclass{article}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{float}\n"
        "\\usepackage[a4paper, left=10mm, right=10mm, top=10mm, bottom=10mm]{geometry}\n"
        "\\begin{document}\n"
    )
    with open(os.path.join(output_directory, LATEX_DOCUMENT_FILENAME), "w") as f:
        f.write(latex_content)



def add_to_latex_document(
    output_directory, gnuplot_each_output_directory, projectile, mass, element, residual
):

    latex_content = ""
    formatted_target = "$^{" + mass + "}$" + element 
    formatted_residual = "$^{" +  str(int(residual[1])) + residual[2] + "}" + residual[0]
    formatted_reaction = formatted_target + "(" + projectile + ",X)" + formatted_residual
    label_xs = f"appfig:x{mass}{element}{residual}{''.join(residual)}"
    label_kai = f"appfig:kai{mass}{element}{residual}{''.join(residual)}"

    # section_title = f"{projectile} induced {mass}{element} → {int(residual[1])}{residual[2]}{residual[0]}"
    latex_content = f"\\subsubsection{{{formatted_reaction}}}\n"

    # First subsection: Cross Section Plot
    # latex_content += "\\subsection{Cross Section Plot}\n"
    plot_dir = os.path.join(gnuplot_each_output_directory)
    for file_name in os.listdir(plot_dir):
        if file_name.startswith("combined_cross_section_plot_") and file_name.endswith(
            ".png"
        ):
            file_path = os.path.join(plot_dir, file_name)

            if os.path.exists(file_path):
                latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
                latex_content += (
                    f"\\includegraphics[width=0.8\\textwidth]{{{file_path}}}\n"
                )
                latex_content += "\\caption{Cross section plot of " + formatted_reaction + "}\n"
                latex_content += f"\\label{{label_xs}}\n"
                latex_content += "\\end{figure}\n"
            else:
                latex_content += "No Chi Squared Plot was emitted."

    # Second subsection: Chi Squared Calculation for Each Product
    # latex_content += "\\subsection{Chi Squared Calculation for Each Product}\n"
    plot_dir = os.path.join(gnuplot_each_output_directory)
    for file_name in os.listdir(plot_dir):
        if file_name.startswith("chi_squared_vs_input_") and file_name.endswith(".png"):
            file_path = os.path.join(plot_dir, file_name)

            if os.path.exists(file_path):
                latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
                latex_content += (
                    f"\\includegraphics[width=0.8\\textwidth]{{{file_path}}}\n"
                )
                latex_content += "\\caption{Chi Squared Calculation for " + formatted_reaction +  "}\n" 
                latex_content += f"\\label{{label_kai}}\n"
                latex_content += "\\end{figure}\n"
            else:
                latex_content += "No Chi Squared Plot was emitted."

    with open(os.path.join(output_directory, LATEX_DOCUMENT_FILENAME), "a") as f:
        f.write(latex_content)


def add_totalchi_to_latex_document(gnuplot_output_directory):

    section_title = "Total chi squared value from four "
    latex_content = ""
    # latex_content = f"\\section{{{section_title}}}\n"

    plot_dir = os.path.join(gnuplot_output_directory)
    avg_file_path = os.path.join(plot_dir, "chi_squared_total_average_vs_input.png")

    if os.path.exists(avg_file_path):
        latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
        latex_content += f"\\includegraphics[width=\\textwidth]{{{avg_file_path}}}\n"
        latex_content += "\\caption{" + section_title +  "}" 
        latex_content += f"\\label{{label_kai}}\n"
        latex_content += "\\end{figure}\n"
    else:
        latex_content += "No Chi Squared Plot was emitted."

    with open(
        os.path.join(gnuplot_output_directory, LATEX_DOCUMENT_FILENAME), "a"
    ) as f:
        f.write(latex_content)


def add_masschi_to_latex_document(gnuplot_output_directory, j):

    # section_title = f"Chi squared value vs Residual Mass"
    latex_content = ""
    # latex_content = f"\\section{{{section_title}}}\n"

    plot_dir = os.path.join(gnuplot_output_directory)
    avg_file_path = os.path.join(plot_dir, f"chi_squared_value_vs_mass_inp{j}.png")

    if os.path.exists(avg_file_path):
        latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
        latex_content += f"\\includegraphics[width=\\textwidth]{{{avg_file_path}}}\n"
        latex_content += "\\caption{Chi squared value vs Residual Mass}\n" 
        # latex_content += f"\\label{{label_kai}}\n"
        latex_content += "\\end{figure}\n"
    else:
        latex_content += "No Chi Squared vs Mass Plot was emitted."

    with open(
        os.path.join(gnuplot_output_directory, LATEX_DOCUMENT_FILENAME), "a"
    ) as f:
        f.write(latex_content)


def end_latex_document(output_directory):
    latex_content = "\\end{document}\n"
    with open(os.path.join(output_directory, LATEX_DOCUMENT_FILENAME), "a") as f:
        f.write(latex_content)


def add_table_to_latex_document(gnuplot_output_directory, chi2_values_list):
    section_title = "Chi-Squared Values Table"
    latex_content = ""
    # latex_content = f"\\section{{{section_title}}}\n"

    # Begin the table
    latex_content += f"\\begin{{table}}[H]\n\\centering\n"
    latex_content += (
        f"\\begin{{tabular}}{{|c|" + "c|" * len(chi2_values_list[0]) + "}}\n"
    )
    latex_content += "\\hline\n"

    # Table headers
    # headers = "number" + ["Residual Mass"] + [f"Input {i+1}" for i in range(len(chi2_values_list[0]))]
    # latex_content += f" & ".join(headers) + " \\\\\n"
    latex_content += "\\textbf{number} & \\textbf{Residual Mass} & \\textbf{Input 1} & \\textbf{Input 2} & \\textbf{Input 3} & \\textbf{Input 4} & \\textbf{Input 5} \\\n"
    latex_content += "\\hline\n"

    # Table content
    for i, row in enumerate(chi2_values_list, start=1):
        formatted_row = [f"{x:.2f}" if x != 0 else "-" for x in row]
        latex_content += f"{i} & " + " & ".join(formatted_row) + " \\\\\n"

    # End the table
    latex_content += "\\end{tabular}\n"
    latex_content += "\\caption{Residual mass vs chi-squared.}\n"
    latex_content += "\\label{tab:chi2_values}\n"
    latex_content += "\\end{table}\n"

    with open(
        os.path.join(gnuplot_output_directory, LATEX_DOCUMENT_FILENAME), "a"
    ) as f:
        f.write(latex_content)


def add_ratio_to_latex_document(gnuplot_output_directory, column_idx):
    """Add ratio plot to the LaTeX document."""
    section_title = f"Ratio of Input {column_idx} to Input 2 vs Residual Mass"
    # latex_content = f"\\section{{{section_title}}}\n"

    plot_dir = os.path.join(gnuplot_output_directory)
    ratio_file_path = os.path.join(plot_dir, f"ratio_vs_mass_col{column_idx}.png")

    if os.path.exists(ratio_file_path):
        latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
        latex_content += f"\\includegraphics[width=\\textwidth]{{{ratio_file_path}}}\n"
        latex_content += f"\\caption{{section_title}}\n" 
        latex_content += "\\end{figure}\n"
    else:
        latex_content += "No Ratio Plot was emitted."

    with open(
        os.path.join(gnuplot_output_directory, LATEX_DOCUMENT_FILENAME), "a"
    ) as f:
        f.write(latex_content)



# def add_to_latex_document(
#     output_directory, gnuplot_each_output_directory, projectile, mass, element
# ):

#     latex_content = ""
#     figure_caption = "$^{" + mass + "}$" + element + "(" + projectile + "X)"
#     # latex_content = f"\\section{{{section_title}}}\n"

#     # First subsection: Cross Section Plot
#     # latex_content += "\\subsection{Cross Section Plot}\n"
#     plot_dir = os.path.join(gnuplot_each_output_directory)
#     plot_files1 = [
#         file_name
#         for file_name in os.listdir(plot_dir)
#         if file_name.startswith("combined_cross_section_plot_")
#         and file_name.endswith(".png")
#     ]

#     sorted_plot_files1 = sorted(
#         plot_files1,
#         key=lambda x: int(os.path.basename(x).split("_")[-1].split(".")[0]),
#         reverse=True,
#     )

#     plot_files2 = [
#         file_name
#         for file_name in os.listdir(plot_dir)
#         if file_name.startswith("chi_squared_vs_input_") and file_name.endswith(".png")
#     ]

#     sorted_plot_files2 = sorted(
#         plot_files2,
#         key=lambda x: int(os.path.basename(x).split("_")[-1].split(".")[0]),
#         reverse=True,
#     )

#     for file_name in sorted_plot_files1:
#         file_path = os.path.join(plot_dir, file_name)
#         latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
#         latex_content += f"\\includegraphics[width=\\textwidth]{{{file_path}}}\n"
#         latex_content += f"\\caption{{figure_caption}}\\label{{}}"
#         latex_content += "\\end{figure}\n"

#     # Second subsection: Chi Squared Calculation for Each Product
#     latex_content += "\\subsection{Chi Squared Calculation for Each Product}\n"
#     for file_name in sorted_plot_files2:
#         file_path = os.path.join(plot_dir, file_name)
#         latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
#         latex_content += f"\\includegraphics[width=\\textwidth]{{{file_path}}}\n"
#         latex_content += "\\end{figure}\n"

#     # Last subsection: Averaged Chi Squared Calculation
#     latex_content += "\\subsection{Averaged Chi Squared Calculation}\n"
#     avg_file_path = os.path.join(plot_dir, "chi_squared_average_vs_input.png")
#     if os.path.exists(avg_file_path):
#         latex_content += f"\\begin{{figure}}[H]\n\\centering\n"
#         latex_content += f"\\includegraphics[width=\\textwidth]{{{avg_file_path}}}\n"
#         latex_content += "\\end{figure}\n"

#     with open(os.path.join(output_directory, LATEX_DOCUMENT_FILENAME), "a") as f:
#         f.write(latex_content)
