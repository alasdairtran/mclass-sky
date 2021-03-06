mclearn
=======
**Multiclass Active Learning Algorithms with Application in Astronomy.**

:Contributors: `Alasdair Tran <http://alasdairtran.com>`_,
               `Cheng Soon Ong <http://www.ong-home.my>`_,
               `Lee Wei Yen <https://weiyen.net>`_
:License: This package is distributed under a a 3-clause ("Simplified" or "New") BSD license.
:Source: `<https://github.com/chengsoonong/mclass-sky>`_
:Doc: `<https://mclearn.readthedocs.org/en/latest/>`_
:Thesis: `Photometric Classification with Thompson Sampling`_ by Alasdair Tran

.. image:: https://travis-ci.org/chengsoonong/mclass-sky.svg
    :target: https://travis-ci.org/chengsoonong/mclass-sky

.. image:: https://coveralls.io/repos/chengsoonong/mclass-sky/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/chengsoonong/mclass-sky?branch=master

.. image:: https://zenodo.org/badge/doi/10.5281/zenodo.58500.svg
   :target: http://dx.doi.org/10.5281/zenodo.58500

       
Introduction
------------
**mclearn** is a Python package that implement selected multiclass active learning
algorithms, with a focus in astronomical data. For a quick overview of how
**mclearn** works, have a look at the `Getting Started`_ notebook.


Installation
------------
The dependencies are Python 3.4, numpy, pandas, matplotlib, seaborn, ephem, scipy, ipython,
and scikit-learn. It's best to first install the Anaconda distribution for Python 3,
then install **mclearn** using pip::

  pip install mclearn



Datasets
--------
Throughout the experiments, we will be using the dataset from the Sloan Digital Sky Survey.
Due to their size, the following datasets are not included in this repo: ::

  projects/alasdair/data/
  │   sdss.h5
  │   sdss_dr7_photometry_source.csv.gz
  │   sdss_full.h5  
  │   sdss_subclass.h5

The main dataset :code:`sdss.h5` is avaliable on `Zenodo <http://dx.doi.org/10.5281/zenodo.58500>`_:


Notebooks
---------

The following nine notebooks accompany Alasdair's thesis on
`Photometric Classification with Thompson Sampling`_.

1. `Dataset Preparation`_
    We provide instruction on how to obtain the SDSS dataset from the Sloan SkySever.
    We then clean up the data and convert the `csv` files to HDF5 for quicker reading.
    We also do some cleaning up of the raw data from the VST ATLAS survey.

2. `Exploratory Data Analysis`_
    To get a feel for the data, we plot the distributions of the classes (Galaxy, Quasar, Star).
    We will see that the data is quite unbalanced, with three times as many galaxies as quasars.
    A distinction is made between photometry and spectroscopy. We also use PCA to reduce the
    data down to two dimensions.

3. `Dust Extinction`_
    TDust extinction is a potential
    problem in photometry, so we compare three sets of reddening corrections (SFD98, SF11, and
    W14) to see which set is best at removing the bias. It turns out that there are no
    significant differences between the three extinction vectors.

4. `Learning Curves`_
    To see how random sampling performs, we construct learning curves for SVMs, Logistic
    Regression, and Random Forest. A grid search with a 5-fold cross validation
    is performed to choose the best hyperparameters for the SVM and Logistic Regression.
    We also do a polynomial transformation of degree 2 and 3 on the features.

5. `Class Proportion Estimation`_
    We predict the classes of the 800,000 million unlabelled SDSS objects using a random
    forest.

6. `Active Learning with SDSS`_
    We look at six active learning heuristics and see how well they perform in the 
    SDSS dataset.

7. `Active Learning with VST ATLAS`_
    We look at six active learning heuristics and see how well they perform in the 
    VST ATLAS dataset.

8. `Thompson Sampling with SDSS`_
    We know examine the six active learning heuristics under the multi-arm bandit
    setting with Thompson sampling and using the SDSS dataset.

9. `Thompson Sampling with VST ATLAS`_
    We repeat the same Thompson sampling experiment with the VST ATLAS dataset


.. _Photometric Classification with Thompson Sampling:
   https://alasdairtran.github.io/mclearn/tran15honours-thesis.pdf
.. _Getting Started:
   projects/alasdair/notebooks/getting_started.ipynb
.. _Dataset Preparation:
   projects/alasdair/notebooks/01_dataset_prepration.ipynb
.. _Exploratory Data Analysis:
   projects/alasdair/notebooks/02_exploratory_analysis.ipynb
.. _Dust Extinction:
   projects/alasdair/notebooks/03_dust_extinction.ipynb
.. _Learning Curves:
   projects/alasdair/notebooks/04_learning_curves.ipynb
.. _Class Proportion Estimation:
   projects/alasdair/notebooks/05_class_proportion_estimation.ipynb
.. _Active Learning with SDSS:
   projects/alasdair/notebooks/06_active_learning_sdss.ipynb
.. _Active Learning with VST ATLAS:
   projects/alasdair/notebooks/07_active_learning_vstatlas.ipynb
.. _Thompson Sampling with SDSS:
   projects/alasdair/notebooks/08_thompson_sampling_sdss.ipynb
.. _Thompson Sampling with VST ATLAS:
   projects/alasdair/notebooks/09_thompson_sampling_vstatlas.ipynb
