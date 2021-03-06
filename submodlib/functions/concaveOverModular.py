# concaveOverModular.py
# Author: Vishal Kaushal <vishal.kaushal@gmail.com>
import numpy as np
import scipy
from .setFunction import SetFunction
import submodlib_cpp as subcp
from submodlib_cpp import ConcaveOverModular 
from submodlib.helper import create_kernel

class ConcaveOverModularFunction(SetFunction):
	"""Implementation of the ConcaveOverModular (COM) function.

	In a :class:`~submodlib.functions.submodularMutualInformation.SubmodularMutualInformationFunction`, although :math:`f` is defined on :math:`\\Omega`, the discrete optimization problem will only be defined on subsets :math:`\mathcal{A} \\subseteq \\mathcal{V}`. Hence we do not need :math:`f` to be submodular everywhere on :math:`\\Omega`, instead it can be *restricted submodular*. When a MutualInformation function is defined using a restricted submodular function :math:`f`, we call it Generalized Submodular Mutual Information function (GMI). Concave Over Modular is a GMI function :cite:`kaushal2021prism` and is defined as:

	This is a reference to :ref:`functions.conditional-gain` function.
	This is a reference to :any:`functions.conditional-gain` function.
	
	.. math::
			I_{f_{\\eta}}(\\mathcal{A}; \\mathcal{Q}) = \\eta \\sum_{i \\in \\mathcal{A}} \\psi(\\sum_{j \\in \\mathcal{Q}}s_{ij}) + \\sum_{j \\in \\mathcal{Q}} \\psi(\\sum_{i \\in \mathcal{A}} s_{ij})
	
	where :math:`\\eta` models query-relevance and diversity trade-off, :math:`\\psi` is a concave function and kernel matrix :math:`S` satisfies :math:`s_{ij} = 1(i == j)` for :math:`i, j \\in \\mathcal{V}` or :math:`i, j \\in \\mathcal{V}^{\\prime}`.
	
	In terms of its modelling capabilities, while GCMI lies at one end of the spectrum favoring query-relevance and FL1MI lies at the other end favoring diversity and query coverage, COM lies somewhere in between.

	.. note::
			GLISTER :cite:`killamsetty2020glister` has an interesting connection with COM (see :cite:`kaushal2021prism`). Also, the joint diversity and query-relevance term in :cite:`lin2011class` is an instance of COM (with square-root as the concave function).

	Parameters
	----------

	n : int
		Number of elements in the ground set
	
	num_queries : int
		Number of query points in the target
	
	query_sijs : ndarray, optional
		Similarity kernel between the ground set and the queries. Dimensionality: n X num_queries. When not provided, it is computed using imageData, queryData and metric.

	imageData : list, optional
		List of size n containing the ground set data elements. imageData[i] should contain the features of element i. It is optional (and is ignored if provided) if query_sijs has been provided.

	queryData : list, optional
		List of size num_queries containing the query elements. queryData[i] should contain the features of query i. It is optional (and is ignored if provided) if query_sijs has been provided.

	metric : string, optional
		Similarity metric to be used for computing the similarity kernel. Default is "cosine". 
	
	magnificationLambda : float, optional
		The value of the query-relevance vs diversity trade-off. Default is 1.

	mode : ConcaveOverModular.Type, optional
		The concave function to be used. Can be ConcaveOverModular.logarithmic, ConcaveOverModular.squareRoot, ConcaveOverModular.inverse. Default is ConcaveOverModular.logarithmic.
	
	"""

	def __init__(self, n, num_queries, query_sijs=None, imageData=None, queryData=None, metric="cosine", magnificationLambda=1, mode=ConcaveOverModular.logarithmic):
		self.n = n
		self.num_queries = num_queries
		self.metric = metric
		self.query_sijs = query_sijs
		self.imageData = imageData
		self.queryData = queryData
		self.magnificationLambda=magnificationLambda
		self.mode = mode
		self.cpp_obj = None
		self.cpp_query_sijs = None
		self.cpp_content = None
		self.effective_ground = None

		if self.n <= 0:
			raise Exception("ERROR: Number of elements in ground set must be positive")

		if self.num_queries < 0:
			raise Exception("ERROR: Number of queries must be >= 0")

		if self.metric not in ['euclidean', 'cosine']:
			raise Exception("ERROR: Unsupported metric. Must be 'euclidean' or 'cosine'")

		if type(self.query_sijs) != type(None): # User has provided query kernel
			if type(self.query_sijs) != np.ndarray:
				raise Exception("Invalid query kernel type provided, must be ndarray")
			if np.shape(self.query_sijs)[0]!=self.n or np.shape(self.query_sijs)[1]!=self.num_queries:
				raise Exception("ERROR: Query Kernel should be n X num_queries")
			if (type(self.imageData) != type(None)) or (type(self.queryData) != type(None)):
				print("WARNING: similarity query kernel found. Provided image and query data matrices will be ignored.")
		else: #similarity query kernel has not been provided
			if (type(self.imageData) == type(None)) or (type(self.queryData) == type(None)):
				raise Exception("Since query kernel is not provided, data matrices are a must")
			if np.shape(self.imageData)[0]!=self.n:
				raise Exception("ERROR: Inconsistentcy between n and no of examples in the given image data matrix")
			if np.shape(self.queryData)[0]!=self.num_queries:
				raise Exception("ERROR: Inconsistentcy between num_queries and no of examples in the given query data matrix")
			
		  #construct queryKernel
			self.query_sijs = np.array(subcp.create_kernel_NS(self.queryData.tolist(),self.imageData.tolist(), self.metric))
		
		#Breaking similarity matrix to simpler native data structures for implicit pybind11 binding
		self.cpp_query_sijs = self.query_sijs.tolist() #break numpy ndarray to native list of list datastructure
		
		if type(self.cpp_query_sijs[0])==int or type(self.cpp_query_sijs[0])==float: #Its critical that we pass a list of list to pybind11
																			#This condition ensures the same in case of a 1D numpy array (for 1x1 sim matrix)
			l=[]
			l.append(self.cpp_query_sijs)
			self.cpp_query_sijs=l

		self.cpp_obj = ConcaveOverModular(self.n, self.num_queries, self.cpp_query_sijs, self.magnificationLambda, self.mode)
		self.effective_ground = set(range(n))