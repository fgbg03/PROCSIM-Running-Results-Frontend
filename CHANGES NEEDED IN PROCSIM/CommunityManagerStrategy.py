from CommunityManager import CommunityManager
from ConsumptionGenerator import ConsumptionGenerator
from Knapsack import Knapsack
import pandas as pd



class CommunityManagerStrategy(CommunityManager):

  def __init__(self, cg, path_steps_minutes, path_steps_after_first, path_steps_after_second):
    """
    This class is a load balancing strategy implemented using Multiple Knapsack (which is a combinatorial optimization problem).
    Taking in consideration the objective functions and constraints, it shifts the consumption of the activities.

    Args:
      cg: Consumption Generator instance (to allow to use its functions)
      path_steps_minutes: path of the resampled consumption profiles (at 1/60Hz)
      path_steps_after_first: path of the consumption profiles after the 1st step of the optimization
      path_steps_after_second: path of the consumption profiles after the 2nd step of the optimization
    """
    self.cg = cg
    self.path_steps_minutes = path_steps_minutes
    self.path_steps_after_first = path_steps_after_first
    self.path_steps_after_second = path_steps_after_second


  def execute(self, save_to_file=False):
    """
    Executes the optimization process (implemented strategy using Multiple Knapsack):
    1) First step
    - Prepares the input (arrays) for the process (bin_capacities, bin_maximums, timeslots_number, flexibitilies, items_max, etc)
    - Calls the Knapsack class with the input processed (execute_knapsack function)
    - Updates the consumption profiles based on the output of the knapsack
    2) Second Step
    - Prepares the input (arrays) for the process (bin_capacities, bin_maximums, timeslots_number, flexibitilies, items_max, etc)
    - Calls the Knapsack class with the input processed (execute_knapsack function)
    - Updates the consumption profiles based on the output of the knapsack
    """

    print("Optimization the community using the implemented strategy")

    fact = 60
    inputs = self.prepare_inputs(fact, save_to_file)

    self.production_baseload = 0.85 * float(inputs.contracted_power)

    exec = Knapsack(inputs.dates, inputs.items, inputs.bins_capacities, inputs.timeslot_numbers, inputs.bins_maximum, inputs.items_max, self.production_baseload, fact, inputs.n_bins_per_hour, inputs.flexibilities)
    otimization = exec.execute_knapsack(1)

    # Remove all the consumption (all timeslots - placed and not placed ones)
    # Add the consumption of the placed timeslots (just the ones that were placed by the optimization process)
    self.placed_timeslots = otimization[1]
    self.not_placed_timeslots = otimization[2]

    # showNetloadGraph('output/minute/netload.csv')

    updt = self.create_profiles_after_strategy(self.placed_timeslots, self.timeslots, self.path_steps_minutes, self.path_steps_after_first, self.path_steps_minutes.split("/")[-1], self.path_steps_after_first.split("/")[-1], True, inputs.n_bins_per_hour, fact)
    self.placed_timeslots_array = updt[0]
    df_flexible = updt[1]

    # prepare dates and timeslots for the second optimization (the ones that were not placed in the first optimization)
    tmp_index = -1
    dates_second_optim = []
    items_second_optim = []
    numbers_second_optim = []
    items_max_second_optim = []
    flexibilities_second_optim = []
    count = 0
    for tim in self.not_placed_timeslots:

      if (tmp_index != int(float(tim.split("-")[0]))):
        tmp_dates = []
        tmp_weights = []
        tmp_nums = []
        tmp_max = []
        tmp_flexibility = []

      tmp_dates.append(int(float(tim.split("-")[3])))
      tmp_weights.append(float(tim.split("-")[2]))
      tmp_nums.append(int(float(tim.split("-")[0])))
      tmp_max.append(float(tim.split("-")[6]))
      tmp_flexibility.append(tim.split("-")[8])

      if (count == int(float(tim.split("-")[4])) - 1):
        dates_second_optim.append(tmp_dates)
        items_second_optim.append(tmp_weights)
        numbers_second_optim.append(tmp_nums)
        items_max_second_optim.append(tmp_max)
        flexibilities_second_optim.append(tmp_flexibility)
        count = 0
      else:
        count = count + 1
      tmp_index = int(float(tim.split("-")[0]))

    netload_second_optim = pd.read_csv(self.path_steps_after_first + '/netload.csv', sep=';')
    netload_second_optim.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload']

    # Update Production after first optimization (in order to update bin capacities)
    # Remove flexible consumption from netload (update production after optimization by removing placed timeslots consumption
    bins_capacities_second_optimization = self.calculate_bin_used_capacity(inputs.bins_capacities, self.placed_timeslots, self.production_baseload, inputs.n_bins_per_hour)
    bins_maximum_second_optimization = self.get_production_max_after_first_optimization(netload_second_optim, inputs.first_date, self.production_baseload, inputs.n_bins_per_hour, fact)


    print("Community Flexibilities (2nd):")
    print(flexibilities_second_optim)
    print("Bin Capacities (2nd):")
    print(bins_capacities_second_optimization)
    print("Bin Maximum (2nd):")
    print(bins_maximum_second_optimization)
    print("Dates (2nd):")
    print(dates_second_optim)
    print("Timeslots (2nd):")
    print(items_second_optim)
    print("Timeslots Maximum (2nd):")
    print(items_max_second_optim)
    print("Numbers (2nd):")
    print(numbers_second_optim)

    # showNetloadGraph('output/afteroptimization/netload.csv')

    if (len(items_second_optim) > 0 and len(dates_second_optim) > 0):
      # Second Optimization
      second_exec = Knapsack(dates_second_optim, items_second_optim, bins_capacities_second_optimization, numbers_second_optim,
                            bins_maximum_second_optimization, items_max_second_optim, self.production_baseload, fact,
                            inputs.n_bins_per_hour, flexibilities_second_optim)
      second_optim = second_exec.execute_knapsack(2)

      self.second_placed_timeslots = second_optim[1]
      self.second_not_placed_timeslots = second_optim[2]

      print("Not Placed 2nd:")
      print(self.second_not_placed_timeslots)

      updt = self.create_profiles_after_strategy(self.second_placed_timeslots, self.timeslots,
                                                   self.path_steps_after_first, self.path_steps_after_second,
                                                   self.path_steps_after_first.split("/")[-1], self.path_steps_after_second.split("/")[-1], False, inputs.n_bins_per_hour,
                                                   fact)
      self.second_placed_timeslots_array = updt[0]
      # showNetloadGraph('output/aftersecoptimization/netload.csv')

    # print(timeslots)
    # community = ConsumptionGenerator.get_community()
    # ConsumptionGenerator.show_community_graph(community, 'output/minute/house')
    # ConsumptionGenerator.show_community_graph(community, 'output/afteroptimization/house')

    return [df_flexible]
