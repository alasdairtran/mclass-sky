""" Some general standard classifier routines for astronomical data. """

import mclearn
import pickle
import gc
import numpy as np
from sklearn import metrics
from pandas import DataFrame, MultiIndex
import matplotlib.pyplot as plt
from IPython.display import display
from sklearn.preprocessing import PolynomialFeatures
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC, LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle


def train_classifier(data, feature_names, class_name, train_size, test_size, output='',
    random_state=None, coords=True, recall_maps=True, classifier=None, correct_baseline=None,
    balanced=True, returns=['correct_boolean', 'confusion_test'],
    pickle_path=None):
    """ Standard classifier routine.

        Parameters
        ----------
        data : DataFrame
            The DataFrame containing all the data.

        feature_names : array
            A list of column names in data that are used as features.

        class_name : str
            The column name of the target.

        train_size : int
            The size of the training set.

        test_size : int
            The size of the test set.

        output : str
            The name that will be attached to the path of the saved plots.

        random_state : int
            The value of the random state (used for reproducibility).

        coords : bool
            Whehter coordinates are part of the features.

        recall_maps : bool
            Wheter to make a map of recall scores.

        classifier : Classifier object
            An initialised scikit-learn Classifier object.

        correct_baseline : array
            If we want to compare our results to some baseline, supply the default predicted data here.

        balanced : bool
            Whether to make the training and test set balanced.

        Returns
        -------
        correct_boolean : array
            The boolean array indicating which test exmaples were correctly predicted.

        confusion_test : array
            The confusion matrix on the test examples.

    """
    if balanced:
        X_train, X_test, y_train, y_test = mclearn.balanced_train_test_split(
            data, feature_names, class_name, train_size, test_size, random_state=random_state)
    else:
        X_train, X_test, y_train, y_test = train_test_split(np.array(data[feature_names]),
            np.array(data[class_name]), train_size=train_size, test_size=test_size, random_state=random_state)

    if not classifier:
        classifier = RandomForestClassifier(
            n_estimators=300, n_jobs=-1, class_weight='subsample', random_state=random_state)

    if coords:
        coords_train = X_train[:, 0:2]
        coords_test = X_test[:, 0:2]
        X_train = X_train[:, 2:]
        X_test = X_test[:, 2:]


    correct_boolean, confusion_test = print_classification_result(X_train, X_test, y_train,
        y_test, recall_maps, classifier, correct_baseline, coords_test, output)


    if pickle_path:
        with open(pickle_path, 'wb') as f:
            pickle.dump(classifier, f, protocol=4) 

    results = []
    if 'classifier' in returns:
        results.append(classifier)
    if 'correct_boolean' in returns:
        results.append(correct_boolean)
    if 'confusion_test' in returns:
        results.append(confusion_test)

    return results


def print_classification_result(X_train, X_test, y_train, y_test,
    recall_maps=True, classifier=None, correct_baseline=None, coords_test=None, output=''):
    """ Train the specified classifier and print out the results.

        Parameters
        ----------
        X_train : array
            The feature vectors (stored as columns) in the training set.
            
        X_test : array
            The feature vectors (stored as columns) in the test set.
            
        y_train : array
            The target vector in the training set.
            
        y_test : array
            The target vector in the test set.

        recall_maps : bool
            Wheter to make a map of recall scores.

        classifier : Classifier object
            A classifier object that will be used to train and test the data.
            It should have the same interface as scikit-learn classifiers.

        correct_baseline : array
            If we want to compare our results to some baseline, supply the default
            predicted data here.

        coords_test : array
            The coordinates of the test examples used in mapping.

        output : str
            The name that will be attached to the path of the saved plots.

        Returns
        -------
        correct_boolean : array
            The boolean array indicating which test exmaples were correctly predicted.

        confusion_test : array
            The confusion matrix on the test examples.
    """

    # train and test
    classifier.fit(X_train, y_train)
    y_pred_test = classifier.predict(X_test)
    confusion_test = metrics.confusion_matrix(y_test, y_pred_test)
    balanced_accuracy = mclearn.balanced_accuracy_expected(confusion_test)

    # put confusion matrix in a DataFrame
    classes = ['Galaxy', 'Quasar', 'Star']
    pred_index = MultiIndex.from_tuples(list(zip(['Predicted'] * 3, classes)))
    act_index = MultiIndex.from_tuples(list(zip(['Actual'] * 3, classes)))
    confusion_features_df = DataFrame(confusion_test, columns=pred_index, index=act_index)

    # display results
    class_names = ['Galaxy', 'Star', 'Quasar']
    print('Here\'s the confusion matrix:')
    display(confusion_features_df)
    print('The balanced accuracy rate is {:.2%}.'.format(balanced_accuracy))
    print('Classification report:')
    print(classification_report(y_test, y_pred_test, class_names, digits=4))

    correct_boolean = y_test == y_pred_test

    # plot the recall maps
    if recall_maps:
        if correct_baseline is None:
            print('Recall Maps of Galaxies, Stars, and Quasars, respectively:')
            mclearn.plot_recall_maps(coords_test, y_test, y_pred_test, class_names, output,
                correct_boolean, vmin=0.7, vmax=1, mincnt=None, cmap=plt.cm.YlGn)
        else:
            print('Recall Improvement Maps of Galaxies, Stars, and Quasars, respectively:')
            correct_diff = correct_boolean.astype(int) - correct_baseline.astype(int)
            mclearn.plot_recall_maps(coords_test, y_test, y_pred_test, class_names, output,
                correct_diff, vmin=-0.2, vmax=+0.2, mincnt=20, cmap=plt.cm.RdBu)

    return correct_boolean, confusion_test


def learning_curve(sample_sizes, data, feature_cols, class_col, classifier, random_state=None,
    normalise=True, degree=1, pickle_path='learning_curve.pickle'):
    """ Compute the learning curve of a classiifer.

        Parameters
        ----------
        sample_sizes : array
            The list of the sample sizes that the classifier will be trained on.

        data : DataFrame
            The DataFrame containing all the data.

        feature_names : array
            A list of column names in data that are used as features.

        class_name : str
            The column name of the target.

        classifier : Classifier object
            A classifier object that will be used to train and test the data.
            It should have the same interface as scikit-learn classifiers.

        random_state : int
            The value of the Random State (used for reproducibility).

        normalise : boolean
            Whether we should first normalise the data to zero mean and unit variance.

        degree : int
            If greater than 1, the data will first be polynomially transformed
            with the given degree.

        pickle_path : str
            The path where the values of the learning curve will be saved.

        Returns
        -------
        lc_accuracy_test : array
            The list of balanced accuracy scores for the given sample sizes.

    """

    lc_accuracy_test = []

    for i in sample_sizes:
        gc.collect()
        # split data into test set and training set (balanced classes are not enforced)
        X_train, X_test, y_train, y_test = mclearn.balanced_train_test_split(
            data, feature_cols, class_col, train_size=i, test_size=200000, random_state=random_state)
        X_train, y_train = shuffle(X_train, y_train, random_state=random_state*2)
        X_test, y_test = shuffle(X_test, y_test, random_state=random_state*3)

        if normalise:
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

        if degree > 1:
            poly_features = PolynomialFeatures(degree=degree, interaction_only=False, include_bias=True)
            X_train = poly_features.fit_transform(X_train)
            X_test = poly_features.transform(X_test)

        # train the classifier
        classifier.fit(X_train, y_train)

        # apply classifier on test set
        y_pred_test = classifier.predict(X_test)
        confusion_test = metrics.confusion_matrix(y_test, y_pred_test)
        lc_accuracy_test.append(mclearn.performance.balanced_accuracy_expected(confusion_test))

    # pickle learning curve
    with open(pickle_path, 'wb') as f:
        pickle.dump(lc_accuracy_test, f, pickle.HIGHEST_PROTOCOL) 
    
    return lc_accuracy_test


def compute_all_learning_curves(data, feature_cols, target_col):
    """ Compute the learning curves with the most popular classifiers.

        Parameters
        ----------
        data : DataFrame
            The DataFrame containing all the features and target.

        feature_cols : array
            The list of column names of the features.

        target_col: array
            The name of the target column in the DataFrame.
    """

    # define the range of the sample sizes
    sample_sizes = np.concatenate((np.arange(100, 1000, 100), np.arange(1000, 10000, 1000),
                                             np.arange(10000, 100001, 10000), [200000, 300000]))
    sample_sizes_per_class = (sample_sizes / 3).astype(int)

    # due to limited memory, we need to stop earlier when using polynomial kernel of degree 3
    sample_sizes_small = np.concatenate((np.arange(100, 1000, 100), np.arange(1000, 10000, 1000),
                                             np.arange(10000, 40000, 10000)))
    sample_sizes_small_per_class = (sample_sizes_small / 3).astype(int)

    # initialise the classifiers
    svm_rbf = SVC(kernel='rbf', gamma=0.01, C=100, cache_size=2000)
    svm_sigmoid = SVC(kernel='sigmoid', gamma=0.001, C=1000, cache_size=2000)
    svm_poly = LinearSVC(C=0.1, loss='squared_hinge', penalty='l1', dual=False, multi_class='ovr',
                         fit_intercept=True, random_state=21)
    logistic = LogisticRegression(penalty='l1', dual=False, C=1, multi_class='ovr', solver='liblinear', random_state=21)
    forest = RandomForestClassifier(n_estimators=100, n_jobs=-1, class_weight='auto', random_state=21)

    # train SVM with RBF kernel (this will take a few hours)
    lc_svm_rbf = learning_curve(sample_sizes_per_class, data, feature_cols, target_col, svm_rbf, random_state=2,
        normalise=True, pickle_path='pickle/04_learning_curves/lc_svm_rbf.pickle')

    # train SVM with polynomial kernel of degree 2
    lc_svm_poly_2 = learning_curve(sample_sizes_per_class, data, feature_cols, target_col, svm_poly, degree=2,
        random_state=2, normalise=True, pickle_path='pickle/04_learning_curves/lc_svm_poly_2.pickle')

    # train SVM with polynomial kernel of degree 3
    lc_svm_poly_3 = learning_curve(sample_sizes_small_per_class, data, feature_cols, target_col, svm_poly, degree=3,
        random_state=2, normalise=True, pickle_path='pickle/04_learning_curves/lc_svm_poly_3.pickle')

    # train logistic regression with polynomial kernel of degree 2
    lc_logistic_2 = learning_curve(sample_sizes_per_class, data, feature_cols, target_col, logistic, degree=2,
        random_state=2, normalise=True, pickle_path='pickle/04_learning_curves/lc_logistic_2.pickle')

    # train logistic regression with polynomial kernel of degree 3
    lc_logistic_3 = learning_curve(sample_sizes_small_per_class, data, feature_cols, target_col, logistic, degree=3,
        random_state=2, normalise=True, pickle_path='pickle/04_learning_curves/lc_logistic_3.pickle')

    # train a random forest
    lc_forest = learning_curve(sample_sizes_per_class, data, feature_cols, target_col, forest,
        random_state=2, normalise=True, pickle_path='pickle/04_learning_curves/lc_forest.pickle')



def grid_search(X, y, classifier, param_grid, train_size=300, test_size=300, clf_name=None,
    report=True):
    """ A general grid search routine.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        classifier : Classifier object
            A classifier object that will be used to train and test the data.
            It should have the same interface as scikit-learn classifiers.

        param_grid : dict
            Dictionary containing the names of the hyperparameters and their
            associated values which the classifier will be trained with.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        clf_name : str
            The name of the classifier (used for printing of the results).

        report : boolean
            Whether the results (the best hyperparameters) will be printed out.
    """

    cv = StratifiedShuffleSplit(y, n_iter=5, train_size=train_size,
        test_size=test_size, random_state=17)
    grid = GridSearchCV(classifier, param_grid=param_grid, cv=cv)
    grid.fit(X, y)

    if not clf_name:
        clf_name = str(classifier.__class__)

    if report:
        print("The best parameters for {} are {} with a score of {:.2%}.".format(
            clf_name, grid.best_params_, grid.best_score_))
    return grid



def grid_search_svm_rbf(X, y, train_size=300, test_size=300, fig_path='heat.pdf'):
    """ Do a grid search on SVM wih an RBF kernel.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        fig_path : str
            The path where the heat map plot can be saved.
    """

    # define search domain
    C_range = np.logspace(-2, 10, 13)
    gamma_range = np.logspace(-9, 3, 13)
    param_grid_svm = dict(gamma=gamma_range, C=C_range)

    # run grid search
    classifier = SVC(kernel='rbf')
    grid = mclearn.grid_search(X, y, classifier, param_grid_svm, clf_name='SVM RBF')
    scores = mclearn.reshape_grid_socres(grid.grid_scores_, len(C_range), len(gamma_range))

    # plot scores in a heat map
    fig = plt.figure(figsize=(10, 5))
    ax = mclearn.plot_validation_accuracy_heatmap(scores, x_range=gamma_range,
        y_range=C_range, y_label='$C$', x_label='$\gamma$', power10='both')
    fig.savefig(fig_path, bbox_inches='tight')

    # pickle scores
    with open('pickle/04_learning_curves/grid_scores_svm_rbf.pickle', 'wb') as f:
        pickle.dump(scores, f, pickle.HIGHEST_PROTOCOL) 



def grid_search_svm_sigmoid(X, y, train_size=300, test_size=300, fig_path='heat.pdf'):
    """ Do a grid search on SVM wih a sigmoid kernel.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        fig_path : str
            The path where the heat map plot can be saved.
    """

    # define search domain
    C_range = np.logspace(-2, 10, 13)
    gamma_range = np.logspace(-9, 3, 13)
    param_grid_svm = dict(gamma=gamma_range, C=C_range)

    # run grid search
    classifier = SVC(kernel='sigmoid')
    grid = mclearn.grid_search(X, y, classifier, param_grid_svm, clf_name='SVM Sigmoid')
    scores = mclearn.reshape_grid_socres(grid.grid_scores_, len(C_range), len(gamma_range))

    # plot scores in a heat map
    fig = plt.figure(figsize=(10, 5))
    ax = mclearn.plot_validation_accuracy_heatmap(scores, x_range=gamma_range,
        y_range=C_range, y_label='$C$', x_label='$\gamma$', power10='both')
    fig.savefig(fig_path, bbox_inches='tight')

    # pickle scores
    with open('pickle/04_learning_curves/grid_scores_svm_sigmoid.pickle', 'wb') as f:
        pickle.dump(scores, f, pickle.HIGHEST_PROTOCOL) 



def grid_search_svm_poly_degree(X, y, param_grid, degree=2, train_size=300, test_size=300):
    """ Do a grid search on a Linear SVM given the specified polynomial transformation.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        param_grid : dict
            Dictionary containing the names of the hyperparameters and their
            associated values which the classifier will be trained with.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        Returns
        -------
        scores_flat : array
            List of scores of all possible cominbations of the hyperparameters.
    """

    # transform features to polynomial space
    poly_features = PolynomialFeatures(degree=degree, interaction_only=False, include_bias=True)
    X_poly = poly_features.fit_transform(X)

    # run grid search on various combinations
    classifier = LinearSVC(dual=False, fit_intercept=True, multi_class='ovr',
        loss='squared_hinge', penalty='l1', random_state=13)
    grid1 = mclearn.grid_search(X_poly, y, classifier, param_grid,
        train_size=train_size, test_size=test_size, report=False)

    classifier = LinearSVC(dual=False, fit_intercept=True, multi_class='ovr',
        loss='squared_hinge', penalty='l2', random_state=13)
    grid2 = mclearn.grid_search(X_poly, y, classifier, param_grid,
        train_size=train_size, test_size=test_size, report=False)

    classifier = LinearSVC(dual=True, fit_intercept=True, multi_class='ovr',
        loss='hinge', penalty='l2', random_state=13)
    grid3 = mclearn.grid_search(X_poly, y, classifier, param_grid,
        train_size=train_size, test_size=test_size, report=False)

    classifier = LinearSVC(fit_intercept=True, multi_class='crammer_singer',
        random_state=13)
    grid4 = mclearn.grid_search(X_poly, y, classifier, param_grid,
        train_size=train_size, test_size=test_size, report=False)

    # construct the scores
    scores_flat = grid1.grid_scores_ + grid2.grid_scores_ + grid3.grid_scores_ + grid4.grid_scores_

    return scores_flat



def grid_search_svm_poly(X, y, train_size=300, test_size=300, fig_path='heat.pdf'):
    """ Do a grid search on SVM with polynomial transformation of the features.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        fig_path : str
            The path where the heat map plot can be saved.
    """

    # define search domain
    C_range = np.logspace(-6, 6, 13)
    param_grid = dict(C=C_range)

    scores_1 = mclearn.grid_search_svm_poly_degree(
        X, y, param_grid, degree=1, train_size=train_size, test_size=test_size)
    scores_2 = mclearn.grid_search_svm_poly_degree(
        X, y, param_grid, degree=2, train_size=train_size, test_size=test_size)
    scores_3 = mclearn.grid_search_svm_poly_degree(
        X, y, param_grid, degree=3, train_size=train_size, test_size=test_size)

    scores = scores_1 + scores_2 + scores_3
    scores = mclearn.reshape_grid_socres(scores, 12, len(C_range))

    ylabels = ['Degree 1, OVR, Squared Hinge, L1-norm',
               'Degree 1, OVR, Squared Hinge, L2-norm',
               'Degree 1, OVR, Hinge, L2-norm',
               'Degree 1, Crammer-Singer',
               'Degree 2, OVR, Squared Hinge, L1-norm',
               'Degree 2, OVR, Squared Hinge, L2-norm',
               'Degree 2, OVR, Hinge, L2-norm',
               'Degree 2, Crammer-Singer',
               'Degree 3, OVR, Squared Hinge, L1-norm',
               'Degree 3, OVR, Squared Hinge, L2-norm',
               'Degree 3, OVR, Hinge, L2-norm',
               'Degree 3, Crammer-Singer']

    # plot scores on heat map
    fig = plt.figure(figsize=(10, 5))
    ax = mclearn.plot_validation_accuracy_heatmap(scores, x_range=C_range, x_label='$C$', power10='x')
    plt.yticks(np.arange(0, 12), ylabels)
    fig.savefig(fig_path, bbox_inches='tight')

    # pickle scores
    with open('pickle/04_learning_curves/grid_scores_svm_poly.pickle', 'wb') as f:
        pickle.dump(scores, f, pickle.HIGHEST_PROTOCOL) 



def grid_search_logistic_degree(X, y, param_grid, degree=2, train_size=300, test_size=300):
    """ Do a grid search on Logistic Regression given the specified polynomial transformation.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        param_grid : dict
            Dictionary containing the names of the hyperparameters and their
            associated values which the classifier will be trained with.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        Returns
        -------
        scores_flat : array
            List of scores of all possible cominbations of the hyperparameters.
    """

    # transform features to polynomial space
    poly_features = PolynomialFeatures(degree=degree, interaction_only=False, include_bias=True)
    X_poly = poly_features.fit_transform(X)

    # run grid search
    classifier = LogisticRegression(fit_intercept=True, dual=False, solver='liblinear',
        multi_class='ovr', penalty='l1', random_state=51)
    grid1 = mclearn.grid_search(X_poly, y, classifier, param_grid, report=False)

    classifier = LogisticRegression(fit_intercept=True, dual=False, solver='liblinear',
        multi_class='ovr', penalty='l2', random_state=51)
    grid2 = mclearn.grid_search(X_poly, y, classifier, param_grid, report=False)

    classifier = LogisticRegression(fit_intercept=True, dual=False, solver='lbfgs',
        multi_class='multinomial', penalty='l2', random_state=51)
    grid3 = mclearn.grid_search(X_poly, y, classifier, param_grid, report=False)

    # construct the scores
    scores_flat = grid1.grid_scores_ + grid2.grid_scores_ + grid3.grid_scores_

    return scores_flat


def grid_search_logistic(X, y, train_size=300, test_size=300, fig_path='heat.pdf'):
    """ Do a grid search on Logistic Regression.

        Parameters
        ----------
        X : array
            The feature matrix of the data.

        y : array
            The target column.

        train_size : int
            The size of the training set in each iteration.

        test_size : int
            The size of the test set in each iteration.

        fig_path : str
            The path where the heat map plot can be saved.
    """

    # define search domain
    C_range = np.logspace(-6, 6, 13)
    param_grid = dict(C=C_range)

    scores_1 = mclearn.grid_search_logistic_degree(
        X, y, param_grid, degree=1, train_size=train_size, test_size=test_size)
    scores_2 = mclearn.grid_search_logistic_degree(
        X, y, param_grid, degree=2, train_size=train_size, test_size=test_size)
    scores_3 = mclearn.grid_search_logistic_degree(
        X, y, param_grid, degree=3, train_size=train_size, test_size=test_size)

    scores = scores_1 + scores_2 + scores_3
    scores = mclearn.reshape_grid_socres(scores, 9, len(C_range))

    ylabels = ['Degree 1, OVR, L1-norm',
               'Degree 1, OVR, L2-norm',
               'Degree 1, Multinomial, L2-norm',
               'Degree 2, OVR, L1-norm',
               'Degree 2, OVR, L2-norm',
               'Degree 2, Multinomial, L2-norm',
               'Degree 3, OVR, L1-norm',
               'Degree 3, OVR, L2-norm',
               'Degree 3, Multinomial, L2-norm']

    # plot scores on heat map
    fig = plt.figure(figsize=(10, 5))
    ax = mclearn.plot_validation_accuracy_heatmap(scores, x_range=C_range, x_label='$C$', power10='x')
    plt.yticks(np.arange(0, 9), ylabels)
    fig.savefig(fig_path, bbox_inches='tight')

    # pickle scores
    with open('pickle/04_learning_curves/grid_scores_logistic.pickle', 'wb') as f:
        pickle.dump(scores, f, pickle.HIGHEST_PROTOCOL)


def predict_unlabelled_objects(file_path, table, classifier,
    data_cols, feature_cols, chunksize, pickle_paths, fig_paths):
    """ Predict the classes of unlabelled objects given a classifier.

        Parameters
        ----------
        file_path : str
            The path of the HDF5 table that contains the feature matrix.
    """

    sdss_chunks = pd.read_hdf(file_path, table, columns=data_cols, chunksize=chunksize)

    galaxy_map = np.zeros((3600, 3600), dtype=int)
    quasar_map = np.zeros((3600, 3600), dtype=int)
    star_map = np.zeros((3600, 3600), dtype=int)
    object_maps = [galaxy_map, quasar_map, star_map]

    for chunk in sdss_chunks:
        # apply reddening correction and compute key colours
        mclearn.optimise_sdss_features(chunk)
        chunk['prediction'] = forest.predict(chunk[feature_cols])
        
        chunk['ra'] = np.remainder(np.round(chunk['ra'] * 10) + 3600, 3600)
        chunk['dec'] = np.remainder(np.round(chunk['dec'] * 10) + 3600, 3600)
        
        for index, row in chunk.iterrows():
            if row['prediction'] == 'Galaxy':
                galaxy_map[row['ra']][row['dec']] += 1
            elif row['prediction'] == 'Quasar':
                quasar_map[row['ra']][row['dec']] += 1
            elif row['prediction'] == 'Star':
                star_map[row['ra']][row['dec']] += 1
            else:
                print('Invalid prediction.')

    # save our predictions
    for object_map, pickle_path in zip(object_maps, pickle_paths):
        with open(pickle_path, 'wb') as f:
            pickle.dump(object_map, f, protocol=4)

    # print out results
    whole_map = galaxy_map + star_map + quasar_map
    total_galaxies = np.sum(galaxy_map)
    total_quasars = np.sum(quasar_map)
    total_stars = np.sum(star_map)
    total = np.sum(whole_map)
    print('Total number of objects:', total)
    print('Number of predicted as galaxies: {:,} ({:.1%})'.format(total_galaxies, total_galaxies/total))
    print('Number of predicted as quasars: {:,} ({:.1%})'.format(total_quasars, total_quasars/total))
    print('Number of predicted as stars: {:,} ({:.1%})'.format(total_stars, total_stars/total))

    # construct ra-dec coordinates
    ra = np.arange(0, 360, 0.1)
    dec = np.arange(0, 360, 0.1)
    decs, ras = np.meshgrid(dec, ra)
    decs = decs.flatten()
    ras = ras.flatten()


    # plot prediction on ra-dec maps
    object_maps = [whole_map, galaxy_map, quasar_map, star_map]
    for obj_map, fig_path in zip(object_maps, fig_paths):
        fig = plt.figure(figsize=(10,5))
        ax = mclearn.viz.plot_hex_map(ras, decs, C=obj_map.flatten(), gridsize=360,
            reduce_C_function=np.sum, vmin=0, vmax=50000, origin=180,
            milky_way=True)
        fig.savefig(fig_path, bbox_inches='tight', dpi=300)