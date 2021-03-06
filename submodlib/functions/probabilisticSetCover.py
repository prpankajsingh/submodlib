# probabilisticSetCover.py
# Author: Vishal Kaushal <vishal.kaushal@gmail.com>
from .setFunction import SetFunction
from submodlib_cpp import ProbabilisticSetCover

class ProbabilisticSetCoverFunction(SetFunction):
	"""Implementation of the Probabilistic Set Cover submodular function.
	
	This variant of the set cover function is defined as 
	
	.. math::
			f_{psc}(X) = \\sum_{u \\in U} (1 - \\prod_{x \\in X} (1 - p_{xu}))
	
	where :math:`p_{xu}` is the probability with which concept :math:`u` is covered by element :math:`x`. Similar to the set cover function, this function models the coverage aspect of the candidate summary (subset), viewed stochastically and is also monotone submodular.

	The probabilistic set cover function is 
	
	.. math::
			f(A) = \\sum_{i \\in U} w_i(1 - P_i(A))
	
	where :math:`U` is the set of concepts, and :math:`P_i(A) = \\prod_{j \\in A} (1 - p_{ij})`, i.e. :math:`P_i(A)` is the probability that :math:`A` *doesn't* cover concept :math:`i`. Intuitively, PSC is a soft version of the SC, which allows for probability of covering concepts, instead of a binary yes/no, as is the case with SC.

	Parameters
	----------
	n : int
		Number of elements in the ground set
	n_concepts : int
		Number of concepts
	probs : list
		List of probability vectors for each data point / image, each probability vector containing the probabilities with which that data point / image covers each concept
	weights : list
		Weight :math:`w_i` of each concept
	
	"""

	def __init__(self, n, probs, num_concepts, concept_weights=None):
		self.n = n
		self.probs = probs
		self.num_concepts = num_concepts
		self.concept_weights = concept_weights
		self.cpp_obj = None

		if self.n <= 0:
			raise Exception("ERROR: Number of elements in ground set must be positive")

		if self.n != len(self.probs):
			raise Exception("ERROR: Mismtach between n and len(probs)")

		if self.num_concepts != len(self.probs[0]):
			raise Exception("ERROR: Mismtach between num_concepts and len(probs[0])")
		
		if (type(self.concept_weights) != type(None)):
			if self.num_concepts != len(self.concept_weights):
			    raise Exception("ERROR: Mismtach between num_conepts and len(concept_weights)")
		else:
			self.concept_weights = [1] * self.num_concepts

		self.cpp_obj = ProbabilisticSetCover(self.n, self.probs, self.num_concepts, self.concept_weights)

		self.effective_ground = set(range(n))

	