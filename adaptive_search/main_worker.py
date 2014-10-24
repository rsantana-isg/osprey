from __future__ import print_function
import sys
import argparse
import traceback
from socket import gethostname
from getpass import getuser
from datetime import datetime

from six import iteritems
from six.moves import cStringIO

from .config import Config
from .trials import Trial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to worker config file (yaml)')
    parser.parse_args()
    parser.set_defaults(func=execute)
    args = parser.parse_args()
    args_func(args, parser)


def execute(args, parser):
    # Load the config file and extract the fields
    config = Config(args.config)
    config.check_fields()
    estimator = config.estimator()
    session = config.trials()
    cv = config.cv()
    bounds = config.search_space()
    engine = config.search_engine()
    seed = config.search_seed()

    print('Loading dataset')
    dataset = config.dataset()

    for i in range(1):
        print('='*78)

        history = [[t.parameters, t.mean_cv_score]
                   for t in session.query(Trial).all()]
        print('History contains %d trials' % len(history))

        params = engine(history, bounds, seed)
        print('Selected parameters: %r' % params)

        run_single_trial(
            estimator=estimator, dataset=dataset, params=params,
            cv=cv, session=session)


def run_single_trial(estimator, dataset, params, cv, session):
    from sklearn.base import clone
    from sklearn.grid_search import GridSearchCV

    # make sure we get _all_ the parameters, including defaults on the
    # estimator class
    params = clone(estimator).set_params(**params).get_params()

    t = Trial(status='PENDING', parameters=params, host=gethostname(),
                     user=getuser(), started=datetime.now())
    session.add(t)
    session.commit()

    try:
        grid = GridSearchCV(
            estimator, param_grid={k: [v] for k, v in iteritems(params)},
            cv=cv, verbose=1, refit=False)
        grid.fit(dataset)
        score = grid.grid_scores_[0]

        t.mean_cv_score = score.mean_validation_score
        t.cv_scores = score.cv_validation_scores.tolist()
        t.status = 'SUCCEEDED'
    except Exception:
        buf = cStringIO()
        traceback.print_exc(file=buf)

        t.traceback = buf.getvalue()
        t.status = 'FAILED'
        print('-'*78, file=sys.stderr)
        print('Exception encountered while fitting model')
        print('-'*78, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print('-'*78, file=sys.stderr)
    finally:
        t.completed = datetime.now()
        t.elapsed = t.completed - t.started
        session.commit()

    return t.status


def args_func(args, p):
    try:
        args.func(args, p)
    except RuntimeError as e:
        sys.exit("Error: %s" % e)
    except Exception as e:
        if e.__class__.__name__ not in ('ScannerError', 'ParserError'):
            message = """\
An unexpected error has occurred, please consider sending the
following traceback to the mixtape GitHub issue tracker at:

        https://github.com/rmcgibbo/mixtape/issues

"""
            print(message, file=sys.stderr)
        raise  # as if we did not catch it
