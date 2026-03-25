# Add the main module
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(base_dir))

from pythonProject.plotters.batch_plotter import plot_from_json

# Batch plotter
name = 'Queue minimization'
scenarios = [
# {'address': 'digital/fixed_size_speculative/Digital-GREEDY-BITRATE_MAXIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-D-BM' ,'style':'-.'},
# {'address': 'digital/fixed_size_speculative/Digital-GREEDY-PF_MAXIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-D-PFM','style':'-.'},
# {'address': 'digital/fixed_size_speculative/Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-D-QPFM','style':'-.'},
{'address': 'digital/fixed_size_speculative/Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-D-QM','style':'-.'},
# {'address': 'digital/none/Digital-GREEDY-BITRATE_MAXIMIZATION-15000,3,5,15(1).json', 'name': '0-D-BM'},
# {'address': 'digital/none/Digital-GREEDY-PF_MAXIMIZATION-15000,3,5,15(1).json', 'name': '0-D-PFM'},
# {'address': 'digital/none/Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-15000,3,5,15(1).json', 'name': '0-D-QPFM'},
{'address': 'digital/none/Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-15000,3,5,15(1).json', 'name': '0-D-QM'},

# {'address': 'hybrid/fixed_size_speculative/Hybrid-GREEDY-BITRATE_MAXIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-H-BM' ,'style':'-.'},
# {'address': 'hybrid/fixed_size_speculative/Hybrid-GREEDY-PF_MAXIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-H-PFM','style':'-.'},
# {'address': 'hybrid/fixed_size_speculative/Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-H-QPFM','style':'-.'},
{'address': 'hybrid/fixed_size_speculative/Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-sub-allocation-15000,3,5,15(1).json', 'name': '1-H-QM','style':'-.'},
# {'address': 'hybrid/none/Hybrid-GREEDY-BITRATE_MAXIMIZATION-15000,3,5,15(1).json', 'name': '0-H-BM'},
# {'address': 'hybrid/none/Hybrid-GREEDY-PF_MAXIMIZATION-15000,3,5,15(1).json', 'name': '0-H-PFM'},
# {'address': 'hybrid/none/Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-15000,3,5,15(1).json', 'name': '0-H-QPFM'},
{'address': 'hybrid/none/Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-15000,3,5,15(1).json', 'name': '0-H-QM'},
]

plot_from_json(scenarios, name, 10)
