import nose.tools
import numpy
import scipy.linalg
import pandas
from palm.blink_factory import SingleDarkBlinkFactory
from palm.blink_parameter_set import SingleDarkParameterSet
from palm.likelihood_judge import LikelihoodJudge
from palm.qit_likelihood_predictor import LikelihoodPredictor
from palm.viterbi_predictor import ViterbiPredictor
from palm.blink_target_data import BlinkTargetData
from palm.scipy_optimizer import ScipyOptimizer

EPSILON = 0.1

@nose.tools.istest
class TestComputeLikelihoodOfBlinkModelWithShortTrajectory(object):
    def compute_log_likelihood(self, parameter_set, traj_file):
        log_ka = parameter_set.get_parameter('log_ka')
        log_kd = parameter_set.get_parameter('log_kd')
        log_kr = parameter_set.get_parameter('log_kr')
        log_kb = parameter_set.get_parameter('log_kb')
        ka = 10**(log_ka)
        kd = 10**(log_kd)
        kr = 10**(log_kr)
        kb = 10**(log_kb)

        #    I   D   B    A
        # I -ka           ka
        # D    -kr        kr
        # B
        # A     kd   kb   -kd-kb
        rate_matrix = numpy.zeros([4,4])
        rate_matrix[0,0] = -ka
        rate_matrix[0,3] = ka
        rate_matrix[1,1] = -kr
        rate_matrix[1,3] = kr
        rate_matrix[3,1] = kd
        rate_matrix[3,2] = kb
        rate_matrix[3,3] = -kd - kb
        rate_matrix = numpy.asmatrix(rate_matrix)
        Q_dd = rate_matrix[0:3,0:3]
        Q_db = rate_matrix[0:3,3:4]
        Q_bd = rate_matrix[3:4,0:3]
        Q_bb = rate_matrix[3:4,3:4]

        total_G = numpy.zeros([1, 3])
        total_G[0,0] = 1.0
        total_G = numpy.asmatrix(total_G)
        trajectory = pandas.read_csv(traj_file)
        for i, segment in enumerate(trajectory.itertuples()):
            class_label = segment[1]
            t = segment[2]
            # if last frame, no transition after this dwell
            if i == (len(trajectory) - 1):
                if class_label == 'dark':
                    G = scipy.linalg.expm(Q_dd * t)
                elif class_label == 'bright':
                    G = scipy.linalg.expm(Q_bb * t)
            # if not last frame, include transition to next observation class
            else:
                if class_label == 'dark':
                    G = scipy.linalg.expm(Q_dd * t) * Q_db
                elif class_label == 'bright':
                    G = scipy.linalg.expm(Q_bb * t) * Q_bd
            total_G = total_G * G
            # print i, class_label, t, total_G
        likelihood = total_G.sum()
        log_likelihood = numpy.log10(likelihood)
        return log_likelihood

    @nose.tools.istest
    def computes_correct_likelihood_of_short_trajectory(self):
        '''This example computes the likelihood of a trajectory
           for a blink model.
        '''
        model_factory = SingleDarkBlinkFactory()
        model_parameters = SingleDarkParameterSet()
        model_parameters.set_parameter('N', 1)
        model_parameters.set_parameter('log_ka', -0.5)
        model_parameters.set_parameter('log_kd', -0.5)
        model_parameters.set_parameter('log_kr', -0.5)
        model_parameters.set_parameter('log_kb', -0.5)
        data_predictor = LikelihoodPredictor()
        target_data = BlinkTargetData()
        target_data.load_data(data_file="./palm/test/test_data/short_blink_traj.csv")
        model = model_factory.create_model(model_parameters)
        trajectory = target_data.get_feature()
        prediction = data_predictor.predict_data(model, trajectory)
        prediction_array = prediction.as_array()
        log_likelihood = prediction_array[0]
        expected_log_likelihood = self.compute_log_likelihood(model_parameters,
                                    "./palm/test/test_data/short_blink_traj.csv")
        delta_LL = expected_log_likelihood - log_likelihood
        error_message = "Expected %.2f, got %.2f" % (expected_log_likelihood,
                                                    log_likelihood)
        nose.tools.ok_(abs(delta_LL) < EPSILON, error_message)
        print error_message

@nose.tools.istest
class TestOptimizeBlinkModel(object):
    def make_score_fcn(self, model_factory, parameter_set,
                       judge, data_predictor, target_data):
        def f(current_parameter_array):
            parameter_set.update_from_array(current_parameter_array)
            current_model = model_factory.create_model(parameter_set)
            score, prediction = judge.judge_prediction(current_model,
                                                       data_predictor,
                                                       target_data)
            print score, parameter_set
            return score
        return f

    # @nose.tools.istest
    # def optimize_parameters_forward_backward_algorithm_test(self):
    #     '''This example optimizes the parameters
    #        of a blink model to maximize the likelihood.
    #     '''
    #     model_factory = SingleDarkBlinkFactory()
    #     initial_parameters = SingleDarkParameterSet()
    #     initial_parameters.set_parameter('N', 10)
    #     initial_parameters.set_parameter_bounds('log_ka', -3.0, 2.0)
    #     initial_parameters.set_parameter_bounds('log_kd', -3.0, 2.0)
    #     initial_parameters.set_parameter_bounds('log_kr', -3.0, 2.0)
    #     initial_parameters.set_parameter_bounds('log_kb', -3.0, 2.0)
    #     judge = LikelihoodJudge()
    #     data_predictor = LikelihoodPredictor()
    #     target_data = BlinkTargetData()
    #     target_data.load_data('palm/test/test_data/stochpy_blink10_traj.csv')
    #     score_fcn = self.make_score_fcn(model_factory, initial_parameters,
    #                                     judge, data_predictor, target_data)
    #     optimizer = ScipyOptimizer()
    #     new_params, score = optimizer.optimize_parameters(score_fcn, initial_parameters)
    #     optimized_model = model_factory.create_model(new_params)
    #     score, prediction = judge.judge_prediction(optimized_model, data_predictor,
    #                                                target_data)
    #     print new_params
    #     print score, prediction

    # @nose.tools.istest
    # def optimize_parameters_viterbi_test(self):
    #     '''This example optimizes the parameters
    #        of a blink model to maximize the likelihood.
    #     '''
    #     model_factory = SingleDarkBlinkFactory()
    #     initial_parameters = SingleDarkParameterSet()
    #     initial_parameters.set_parameter('N', 10)
    #     initial_parameters.set_parameter_bounds('log_ka', -3.0, 2.0)
    #     initial_parameters.set_parameter_bounds('log_kd', -3.0, 2.0)
    #     initial_parameters.set_parameter_bounds('log_kr', -3.0, 2.0)
    #     initial_parameters.set_parameter_bounds('log_kb', -3.0, 2.0)
    #     judge = LikelihoodJudge()
    #     data_predictor = ViterbiPredictor()
    #     target_data = BlinkTargetData()
    #     target_data.load_data('palm/test/test_data/stochpy_blink10_traj.csv')
    #     score_fcn = self.make_score_fcn(model_factory, initial_parameters,
    #                                     judge, data_predictor, target_data)
    #     optimizer = ScipyOptimizer()
    #     new_params, score = optimizer.optimize_parameters(score_fcn, initial_parameters)
    #     optimized_model = model_factory.create_model(new_params)
    #     score, prediction = judge.judge_prediction(optimized_model, data_predictor,
    #                                                target_data)
    #     print new_params
    #     print score, prediction