
# # Linear Model MCMC
# Part of the Bayesian neural networks via MCMC: a Python-based tutorial
# 
# This section of the tutorial covers the development of an MCMC algorithm applied to a simple linear model.


import os, sys
import numpy as np
import pandas as pd
import xarray as xr
from collections import ChainMap
from ipywidgets import interact, fixed, widgets
# visulisation function
sys.path.append('/project')
from functions.visualisations import (
    histogram_trace, plot_linear_data,
    plot_y_timeseries, boxplot_weights,
    plot_ycorr_scatter
)

from publication_results.models.mcmc import MCMC_Linear as MCMC
from publication_results.models.linear_model import LinearModel

################################################################################
################################################################################


def run_linear_model(data_name,n_samples=10000,model_name='linear',seed=2023):
    np.random.seed(seed)
    os.chdir('/project')
    print('Running linear model on {} data'.format(data_name))
    # load the data
    name        = data_name
    train_data   = np.loadtxt("data/{}/train.txt".format(name))
    test_data    = np.loadtxt("data/{}/test.txt".format(name))

    print('Training data shape: {}'.format(train_data.shape))

    ## MCMC Settings and Setup
    burn_in = int(n_samples* 0.5) # number of samples to discard before recording draws from the posterior

    # or load from sunspot data
    x_data = train_data[:,:-1]
    y_data = train_data[:,-1]
    x_test = test_data[:,:-1]
    y_test = test_data[:,-1]

    if name in ['Sunspot','Abalone']:
        layer_sizes = [x_data.shape[1], 1]
        data_case = 'regression'
    elif name in ['Iris']:
        layer_sizes = [x_data.shape[1], 3]
        data_case = 'classification'
    elif name in ['Ionosphere']:
        layer_sizes = [x_data.shape[1], 2]
        data_case = 'classification'
    else:
        raise ValueError('data_case is invalid.')

    # Initialise the MCMC class
    lm = LinearModel(layer_sizes=layer_sizes,data_case=data_case)
    mcmc = MCMC(lm,n_samples, burn_in, x_data, y_data, x_test, y_test)
    # Run the sampler
    results, pred = mcmc.sampler()

    # store results - create an xarray dataset
    n_posterior_samples = results.shape[0]
    mcmc_run = xr.Dataset(
        data_vars=ChainMap(*[{
            _: (('chain','samples'), results.loc[:,_].values.reshape((1,n_posterior_samples))) for _ in results.columns
        }, {
            _: (('samples','train_idx',), pred[_]) for _ in pred if 'train' in _
        }, {
            _: (('samples','test_idx',), pred[_]) for _ in pred if 'test' in _
        }]),
        coords={
            'chain': np.array([0]),
            'samples': np.arange(n_posterior_samples),
            'train_idx': np.arange(x_data.shape[0]),
            'test_idx': np.arange(x_test.shape[0])
        }
    )
    # save the results
    os.makedirs('publication_results/results/{}_model'.format(model_name), exist_ok=True)
    mcmc_run.to_netcdf('publication_results/results/{}_model/mcmc_{}_{}.nc'.format(model_name,name,seed))

    # gather the predicitons into useful variables
    pred_y = pred['train_pred']
    sim_y = pred['train_sim']
    pred_y_test = pred['test_pred']
    sim_y_test = pred['test_sim']

    # save some figures
    fig_dir = 'publication_results/results/{}_model/figures'.format(model_name)
    os.makedirs(fig_dir, exist_ok=True)
    # plot the data with the model predictions from posterior draws
    plot_y_timeseries(
        y_data,
        pred_y,
        dataset_name=name + ' Train',
        ci=True,
        fname=os.path.join(fig_dir,'{}_{}_train.png'.format(name,seed))
    )
    plot_y_timeseries(
        y_test,
        pred_y_test,
        dataset_name=name + ' Test',
        ci=True,
        fname=os.path.join(fig_dir,'{}_{}_test.png'.format(name,seed))
    )

    # Print the train/test RMSE
    if data_case == 'regression':
        print('RMSE: mean (std)')
        train_RMSE = np.array([mcmc.rmse(pred_y[_,:], y_data) for _ in np.arange(pred_y.shape[0])])
        test_RMSE = np.array([mcmc.rmse(pred_y_test[_,:], y_test) for _ in np.arange(pred_y_test.shape[0])])
        print('Train RMSE: {:.5f} ({:.5f})'.format(train_RMSE.mean(),train_RMSE.std()))
        print('Test RMSE: {:.5f} ({:.5f})'.format(test_RMSE.mean(),test_RMSE.std()))  
    elif data_case == 'classification':
        print('Accuracy: mean (std)')
        train_acc = np.array([mcmc.accuracy(pred_y[_,:], y_data) for _ in np.arange(pred_y.shape[0])])
        test_acc = np.array([mcmc.accuracy(pred_y_test[_,:], y_test) for _ in np.arange(pred_y_test.shape[0])])
        print('Train Accuracy: {:.3f}% ({:.3f})'.format(train_acc.mean(),train_acc.std()))
        print('Test Accuracy: {:.3f}% ({:.3f})'.format(test_acc.mean(),test_acc.std()))

################################################################################
################################################################################

if __name__ == '__main__':
    # to run this in the background
    # nohup python ./publication_results/01_run_linear_model.py > ./publication_results/linear_results.out &

    data_cases = ['Iris'] #['Sunspot', 'Abalone', 'Iris', 'Ionosphere'] #
    num_chain = 5 # traceplots - 1, results - 5
    # number of samples to draw from the posterior
    n_samples = 10000 # traceplots - 50000, results - 10000
    model_name = 'linear' # traceplots - 'linear_tp', results - 'linear
    for this_case in data_cases:
        for this_chain in np.arange(num_chain):
            run_linear_model(
                this_case,
                n_samples=n_samples,
                model_name= model_name,
                seed=2023+this_chain
            )

################################################################################
################################################################################
