import nose.tools
import mock
import numpy
import scipy.linalg
from palm.qit_likelihood_predictor import LikelihoodPredictor
from palm.util import ALMOST_ZERO

EPSILON = 1e-3

@nose.tools.istest
def vector_scaled_to_correct_value():
    predictor = LikelihoodPredictor()
    vector = numpy.matrix([0.1, 0.1, 0.1])
    expected_c = 1./numpy.sum(vector)
    expected_scaled_vector = expected_c * vector
    scaled_vector, c = predictor.scale_vector(vector)
    error_args = (scaled_vector, expected_scaled_vector)
    error_message = "Vectors don't match got %s, instead of %s" % error_args
    nose.tools.ok_( numpy.array_equal(scaled_vector, expected_scaled_vector),
                    error_message )
    nose.tools.ok_((c - expected_c) < EPSILON)

@nose.tools.istest
def computes_correct_beta():
    ka = 0.1
    kb = 0.1
    prev_beta = numpy.matrix([1.0])
    mock_model = mock.Mock()
    mock_model.get_numpy_submatrix = submatrix_fcn_factory(ka, kb)
    segment_duration = 1.0 # a reasonable dwell time
    start_class = 'start'
    end_class = 'end'
    predictor = LikelihoodPredictor()
    qit_beta = predictor.compute_beta(mock_model, segment_duration,
                                  start_class, end_class, prev_beta)

    Q_aa = mock_model.get_numpy_submatrix(start_class, start_class)
    Q_ab = mock_model.get_numpy_submatrix(start_class, end_class)
    expected_beta = scipy.linalg.expm(Q_aa * segment_duration) * Q_ab * prev_beta
    error_message = "Expected %s,\ngot %s" % (str(expected_beta), str(qit_beta))
    nose.tools.ok_( numpy.allclose(qit_beta, expected_beta), error_message )

def submatrix_fcn_factory(ka, kb, a_mult=1, b_mult=1):
    def get_submatrices(start_class, end_class):
        '''
            A    B
        A   -ka  ka
        B   kb  -kb
        '''
        whole_matrix = numpy.matrix([[-a_mult*ka, a_mult*ka],
                                     [b_mult*kb, -b_mult*kb]])
        if start_class == 'start':
            row_inds = [0]
        elif start_class == 'end':
            row_inds = [1]
        else:
            print "unexpected start class: %s" % start_class
        if end_class == 'end':
            col_inds = [1]
        elif end_class == 'start':
            col_inds = [0]
        else:
            print "unexpected end class: %s" % end_class
        return whole_matrix[row_inds[0]:row_inds[-1]+1, col_inds[0]:col_inds[-1]+1]
    return get_submatrices
