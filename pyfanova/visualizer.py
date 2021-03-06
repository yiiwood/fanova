import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import os
import logging


class Visualizer(object):

    def __init__(self, fanova):
        self._fanova = fanova
        self._latex_template = '''\documentclass[letterpaper]{article}
\\usepackage{times}
\\usepackage{graphicx}
\\usepackage{epsfig}
\\usepackage{subfigure}
\\usepackage{lscape}
\begin{document}
\title{Functional ANOVA Analysis}
\maketitle
\textbf{When using parts of this document, please cite the functional ANOVA paper (the reference will be available soon; in the meantime please ask Frank for details).}
%begin{figure}[tbp]\\
%begin{center}\\
%includegraphics{" + singleMarginalOutputFile + "}\\
%caption{Marginal predictions for parameter " + parameterName.replace("_", "\\_") + ". This marginal explains " + decim2.format(fractionExplainedByThisMarginal) + "\\% of the predictor's total variance. 
%label{fig:" + parameterName + "}}\\
%end{center}\\
%end{figure}\\
\end{document}'''

    def create_all_plots(self, directory, **kwargs):
        """
            Create plots for all main effects.
        """
        assert os.path.exists(directory), "directory %s doesn't exist" % directory

        #categorical parameters
        for param_name in self._fanova.get_config_space().get_categorical_parameters():
            plt.clf()
            outfile_name = os.path.join(directory, param_name.replace(os.sep, "_") + ".png")
            print("creating %s" % outfile_name)
            self.plot_categorical_marginal(param_name)
            plt.savefig(outfile_name)

        #continuous and integer parameters
        params_to_plot = []
        params_to_plot.extend(self._fanova.get_config_space().get_continuous_parameters())
        params_to_plot.extend(self._fanova.get_config_space().get_integer_parameters())
        for param_name in params_to_plot:
            plt.clf()
            outfile_name = os.path.join(directory, param_name.replace(os.sep, "_") + ".png")
            print("creating %s" % outfile_name)
            self.plot_marginal(param_name, **kwargs)
            plt.savefig(outfile_name)

    def create_most_important_pairwise_marginal_plots(self, directory, n=20):
        categorical_parameters = self._fanova.get_config_space().get_categorical_parameters()

        most_important_pairwise_marginals = self._fanova.get_most_important_pairwise_marginals(n)
        for param1, param2 in most_important_pairwise_marginals:
            if param1 in categorical_parameters or param2 in categorical_parameters:
                print("skipping pairwise marginal plot %s x %s, because one of them is categorical" % (param1, param2))
                continue
            outfile_name = os.path.join(directory, param1.replace(os.sep, "_") + "x" + param2.replace(os.sep, "_") + ".png")
            plt.clf()
            print("creating %s" % outfile_name)
            self.plot_pairwise_marginal(param1, param2)
            plt.savefig(outfile_name)

    def plot_categorical_marginal(self, param):
        if isinstance(param, int):
            dim = param
            param_name = self._fanova.get_config_space().get_parameter_names()[dim]
        else:
            if param not in self._fanova.param_name2dmin:
                print("Parameter %s not known" % param)
                return
            dim = self._fanova.param_name2dmin[param]
            param_name = param

        categorical_size = self._fanova.get_config_space().get_categorical_size(param_name)

        labels = self._fanova.get_config_space().get_categorical_values(param)
        
        if param_name not in self._fanova.get_config_space().get_categorical_parameters():
            print("Parameter %s is not a categorical parameter!" % (param_name))

        indices = np.asarray(list(range(categorical_size)))
        width = 0.5
        marginals = [self._fanova.get_categorical_marginal_for_value(param_name, i) for i in range(categorical_size)]
        mean, std = list(zip(*marginals))
        #plt.bar(indices, mean, width, color='red', yerr=std)
        #plot mean
        b = plt.boxplot([[x] for x in mean], 0, '', labels=labels)
        min_y = mean[0]
        max_y = mean[0]
        # blow up boxes 
        for box, std_ in zip(b["boxes"], std):
            y = box.get_ydata()
            y[2:4] = y[2:4] + std_
            y[0:2] = y[0:2] - std_
            y[4] = y[4] - std_
            box.set_ydata(y)
            min_y = min(min_y, y[0] - std_)
            max_y = max(max_y, y[2] + std_)
        
        plt.ylim([min_y, max_y])
        
        #plt.xticks(indices, labels)
        plt.ylabel("Performance")
        plt.xlabel(param_name)

        return plt

    def _check_param(self, param):
        if isinstance(param, int):
            dim = param
            param_name = self._fanova.get_config_space().get_parameter_names()[dim]
        else:
            assert param in self._fanova.param_name2dmin, "param %s not known" % param
            dim = self._fanova.param_name2dmin[param]
            param_name = param

        return (dim, param_name)

    def plot_pairwise_marginal(self, param_1, param_2, lower_bound_1=0, upper_bound_1=1, lower_bound_2=0, upper_bound_2=1, resolution=20):

        dim1, param_name_1 = self._check_param(param_1)
        dim2, param_name_2 = self._check_param(param_2)

        grid_1 = np.linspace(lower_bound_1, upper_bound_1, resolution)
        grid_2 = np.linspace(lower_bound_2, upper_bound_2, resolution)

        zz = np.zeros([resolution * resolution])
        for i, y_value in enumerate(grid_2):
            for j, x_value in enumerate(grid_1):
                zz[i * resolution + j] = self._fanova._get_marginal_for_value_pair(dim1, dim2, x_value, y_value)[0]

        zz = np.reshape(zz, [resolution, resolution])

        display_grid_1 = [self._fanova.get_config_space().unormalize_value(param_name_1, value) for value in grid_1]
        display_grid_2 = [self._fanova.get_config_space().unormalize_value(param_name_2, value) for value in grid_2]

        display_xx, display_yy = np.meshgrid(display_grid_1, display_grid_2)

        fig = plt.figure()
        #ax = fig.gca(projection='3d')
        ax = Axes3D(fig)

        surface = ax.plot_surface(display_xx, display_yy, zz, rstride=1, cstride=1, cmap=cm.jet, linewidth=0, antialiased=False)
        ax.set_xlabel(param_name_1)
        ax.set_ylabel(param_name_2)
        ax.set_zlabel("Performance")
        fig.colorbar(surface, shrink=0.5, aspect=5)
        return plt

    def plot_marginal(self, param, lower_bound=0, upper_bound=1, is_int=False, resolution=100, log_scale=False):
        if isinstance(param, int):
            dim = param
            param_name = self._fanova.get_config_space().get_parameter_names()[dim]
        else:
            if param not in self._fanova.param_name2dmin:
                print("Parameter %s not known" % param)
                return
            dim = self._fanova.param_name2dmin[param]
            param_name = param

        if param_name not in self._fanova.get_config_space().get_integer_parameters() and param_name not in self._fanova.get_config_space().get_continuous_parameters():
            print("Parameter %s is not a continuous or integer parameter!" % (param_name)) 
            return 
        grid = np.linspace(lower_bound, upper_bound, resolution)
        display_grid = [self._fanova.get_config_space().unormalize_value(param_name, value) for value in grid]

        mean = np.zeros(resolution)
        std = np.zeros(resolution)
        for i in range(0, resolution):
            (m, s) = self._fanova.get_marginal_for_value(dim, grid[i])
            mean[i] = m
            std[i] = s
        mean = np.asarray(mean)
        std = np.asarray(std)

        lower_curve = mean - std
        upper_curve = mean + std

        if log_scale or (np.diff(display_grid).std() > 0.000001 and param_name in self._fanova.get_config_space().get_continuous_parameters()):
            #HACK for detecting whether it's a log parameter, because the config space doesn't expose this information
            plt.semilogx(display_grid, mean, 'b')
            #print "printing %s semilogx" % param_name
        else:
            plt.plot(display_grid, mean, 'b')
        plt.fill_between(display_grid, upper_curve, lower_curve, facecolor='red', alpha=0.6)
        plt.xlabel(param_name)

        plt.ylabel("Performance")
        return plt
    
#     def create_pdf_file(self):
#         latex_doc = self._latex_template
#         with open("fanova_output.tex", "w") as fh:
#             fh.write(latex_doc)        
#             subprocess.call('pdflatex fanova_output.tex')
