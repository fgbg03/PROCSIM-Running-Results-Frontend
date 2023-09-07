from abc import ABC, abstractmethod
import pandas as pd
import os
import math
import shutil
import errno
import datetime
from Input import Input
import numpy as np


class CommunityManager(ABC):


  def calculate_bin_used_capacity(self, bins_capacities, placed_timeslots, production_baseload, n_bins_per_hour):
    """
    Updates the bin capacity for the second part of the optimization (increases the production_baseload to the bin capacity of the first part, and subtracts the energy of the placed timeslots in the first step.

    Args:
      bins_capacities: bin capacities of the bins in the 1st step of the optimization
      placed_timeslots: placed timeslots in the 1st step (in order to subtract the energy of them to the bin capacity) - if they are placed, the bin capacity decreases
      production_baseload: value to increment in the bin capacities, which corresponds to the value of energy that can be acquired from the grid in the 2nd step
      n_bins_per_hour: number of bins per hour (parameter of the strategy) to know the quantity of bins in a day (e.g. if bins of 30 minutes, n_bins_per_hour = 2)

    Returns:
      array with x positions in a day (where the number of positions is 24*n_bins_per_hour) with the bin capacity of each bin
    """

    binUsedCapacity = [0] * 24 * n_bins_per_hour

    for bin in range(len(bins_capacities)):
      binUsedCapacity[bin] = bins_capacities[bin]
      binUsedCapacity[bin] += production_baseload

    for timeslot in placed_timeslots:
      tm = timeslot.split("-")
      weight = float(tm[2])
      bin = int(tm[3]) - 1  # bin 1 is 0 position (00:00-00:59)
      binUsedCapacity[bin] -= weight

    return binUsedCapacity


  def get_production_max_after_first_optimization(self, netload_second_optim, fd, production_baseload, n_bins_per_hour, fact):
    """
    Calculates the maximum production peak for each bin of the second step (calculates the maximum in the netload dataframe after updating the profiles of 1st step, and have to increase the production_baseload and decrease the energy of the placed timeslots of the 1st step)

    Args:
      netload_second_optim: dataframe which contains the netload after updating the profiles of the 1st step (to calculate the maximum peak in the 2nd step)
      fd: consumption profile date (to
      production_baseload: value to increment in the bin capacities, which corresponds to the value of energy that can be acquired from the grid in the 2nd step
      n_bins_per_hour: number of bins per hour (parameter of the strategy) to know the quantity of bins in a day (e.g. if bins of 30 minutes, n_bins_per_hour = 2)
      fact: minutes of each bin (e.g. if bins of 30 minutes, fact = 30)

    Returns:
      array with x positions in a day (where the number of positions is 24*n_bins_per_hour) with the bin maximum production peak of each bin
    """

    bins_maximum_second_optimization = []
    for z in range(0, 24):

      startMin = 0
      endMin = fact - 1
      for w in range(0, n_bins_per_hour):
        max = netload_second_optim[
          (netload_second_optim['Date'] >= str(fd) + ' ' + str(z).zfill(2) + ':' + str(startMin).zfill(2) + ':00') & (
                  netload_second_optim['Date'] <= str(fd) + ' ' + str(z).zfill(2) + ':' + str(endMin).zfill(2) + ':00')][
          'Production'].max()
        # demand when the production is max
        binUsage = netload_second_optim.loc[netload_second_optim[
          (netload_second_optim['Date'] >= str(fd) + ' ' + str(z).zfill(2) + ':' + str(startMin).zfill(2) + ':00') & (
                  netload_second_optim['Date'] <= str(fd) + ' ' + str(z).zfill(2) + ':' + str(endMin).zfill(2) + ':00')][
          'Production'].idxmax()]["Demand"]
        bins_maximum_second_optimization.append(max + production_baseload - binUsage)

        startMin = startMin + fact
        endMin = endMin + fact

    return bins_maximum_second_optimization


  def remove_flexible_consumption(self):
    """
    Removes the flexible consumption of the consumption profile, in order to have the baseload consumption (that consumption that can not be shifted.
    In order to do this, the consumption of the flexible appliances are subtracted from the netload and community dataframes (notice that each flexible has it own consumption profile for each house)

    Returns:
      netload dataframe with the non-flexible consumption
    """

    flexible_timeslots = self.cg.get_timeslots(self.cg.get_community(), True)

    df_community = pd.read_csv(self.path_steps_after_first + '/community.csv', sep=';')  # Header=None to indicate that the first row is data and not colummn names
    df_community.columns = ['Date', 'Power']

    df_netload = pd.read_csv(self.path_steps_after_first + '/netload.csv', sep=';')  # Header=None to indicate that the first row is data and not colummn names
    df_netload.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload']


    for timeslot in flexible_timeslots:

      df_appliance = pd.read_csv(self.path_steps_after_first + '/house' + str(timeslot["House"]) + '/' + timeslot["Appliance"] + ".csv", sep=';')  # Header=None to indicate that the first row is data and not colummn names
      df_appliance.columns = ['Date', 'Power']

      df_total = pd.read_csv(self.path_steps_after_first + '/house' + str(timeslot["House"]) + '/total.csv', sep=';')  # Header=None to indicate that the first row is data and not colummn names
      df_total.columns = ['Date', 'Power']

      start_obj = datetime.datetime.strptime(timeslot["Start"], '%Y-%m-%d %H:%M:%S')  # Convert string to datetime object
      end_obj = datetime.datetime.strptime(timeslot["End"], '%Y-%m-%d %H:%M:%S')  # Convert string to datetime object
      obj = start_obj

      while (obj != end_obj + datetime.timedelta(minutes=1)):

        # Update house total consumption
        indexTotal = df_total[df_total.Date == str(obj)].index  # Get index of the row

        df_total.loc[indexTotal, 'Power'] = float(df_total[df_total.Date == str(obj)]["Power"]) - float(df_appliance[df_appliance.Date == str(obj)]["Power"])

        # Update community consumption
        indexCommunity = df_community[df_community.Date == str(obj)].index  # Get index of the row
        df_community.loc[indexCommunity, 'Power'] = float(df_community[df_community.Date == str(obj)]["Power"]) - float(df_appliance[df_appliance.Date == str(obj)]["Power"])


        # Update community netload
        indexNetload = df_netload[df_netload.Date == str(obj)].index  # Get index of the row
        df_netload.loc[indexNetload, 'Demand'] = float(df_netload[df_netload.Date == str(obj)]["Demand"]) - float(df_appliance[df_appliance.Date == str(obj)]["Power"])

        # Update appliance consumption - has to be the last update since the others dataframes use this dataframe
        indexAppliance = df_appliance[df_appliance.Date == str(obj)].index  # Get index of the row
        df_appliance.loc[indexAppliance, 'Power'] = 0

        obj = obj + datetime.timedelta(minutes=1)  # Next minute


      # After all minutes of the appliance updated
      output_directory = os.path.join('', self.path_steps_after_first + '/house' + str(timeslot["House"]))

      outname = os.path.join(output_directory, str(timeslot["Appliance"]) + '.csv')
      df_appliance.to_csv(outname, columns=['Date', 'Power'], sep=";", index=False)

      outname = os.path.join(output_directory, 'total.csv')
      df_total.to_csv(outname, columns=['Date', 'Power'], sep=";", index=False)

    output_directory = os.path.join('', self.path_steps_after_first)
    outname = os.path.join(output_directory, 'community.csv')
    df_community.to_csv(outname, columns=['Date', 'Power'], sep=";", index=False)

    outname = os.path.join(output_directory, 'netload.csv')
    df_netload.to_csv(outname, columns=['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload'], sep=";", index=False)

    return df_netload



  def create_profiles_after_strategy(self, placed_timeslots, all_timeslots_objects, initial_path, final_path, short_initial_path, short_final_path, remove_flex_cons, n_bins_per_hour, fact):
    """
    Implementing the abstract function (from the parent) which updates the profiles after applying the strategy.

    Args:
      placed_timeslots: array of the placed timeslots
      all_timeslots_objects: array of all timeslots with all the information (Start, End, Appliance, Power, House, etc)
      initial_path: path of the minutes (1/60Hz) dataframe (e.g. "(...)/output/minute")
      final_path: path of the dataframe after the strategy (e.g. "(...)/output/afteroptimization")
      short_initial_path: folder of the minutes (1/60Hz) dataframe (e.g. "minutes")
      short_final_path: folder of the dataframe after the strategy e.g. "afteroptimization")
      remove_flex_cons: if True, the flexible consumption will be removed, otherwise the flexible consumption will not be removed (in 1st step, it was True to remove the flexible consumption and in the 2nd step it was False because the flexible consumption has already been removed)
      n_bins_per_hour: number of bins per hour (parameter of the strategy) to know the quantity of bins in a day (e.g. if bins of 30 minutes, n_bins_per_hour = 2)
      fact: minutes of each bin (e.g. if bins of 30 minutes, fact = 30)

    Returns:
      output of update_consumption_profiles_based_on_optimization function
    """
    return self.update_consumption_profiles_based_on_optimization(placed_timeslots, all_timeslots_objects, initial_path, final_path, short_initial_path, short_final_path, remove_flex_cons, n_bins_per_hour, fact)


  def update_consumption_profiles_based_on_optimization(self, placed_timeslots, all_timeslots_objects, initial_path, final_path, short_initial_path, short_final_path, remove_flex_cons, n_bins_per_hour, fact):
    """
    Implementing the function which updates the profiles after applying the strategy.

    Args:
      placed_timeslots: array of the placed timeslots
      all_timeslots_objects: array of all timeslots with all the information (Start, End, Appliance, Power, House, etc)
      initial_path: path of the minutes (1/60Hz) dataframe (e.g. "(...)/output/minute")
      final_path: path of the dataframe after the strategy (e.g. "(...)/output/afteroptimization")
      short_initial_path: folder of the minutes (1/60Hz) dataframe (e.g. "minutes")
      short_final_path: folder of the dataframe after the strategy e.g. "afteroptimization")
      remove_flex_cons: if True, the flexible consumption will be removed, otherwise the flexible consumption will not be removed (in 1st step, it was True to remove the flexible consumption and in the 2nd step it was False because the flexible consumption has already been removed)
      n_bins_per_hour: number of bins per hour (parameter of the strategy) to know the quantity of bins in a day (e.g. if bins of 30 minutes, n_bins_per_hour = 2)
      fact: minutes of each bin (e.g. if bins of 30 minutes, fact = 30)

    Returns:
      array with 2 positions: array of the placed timeslots [0] and flexible dataframe [1]
    """
    # Remove all files of the folder and the folder (before copying the consumption profiles)
    if os.path.exists(final_path):
      shutil.rmtree(final_path)

    # Create the folder
    if not os.path.exists(final_path):
      os.mkdir(final_path)


    # Copy the consumption profiles to after optimization folder in order to change it consumption after the optimization of the timeslots
    try:
      src_files = os.listdir(initial_path)
      for file_name in src_files:
        full_file_name = os.path.join(initial_path, file_name)
        if os.path.isfile(full_file_name):
          shutil.copy(full_file_name, final_path)
        elif os.path.isdir(full_file_name):
          shutil.copytree(full_file_name, os.path.join(final_path, file_name))
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

    # community profile
    # communityBefore = pd.read_csv('output/minute/community.csv', sep=';')  # Header=None to indicate that the first row is data and not colummn names
    # communityBefore.columns = ['Date', 'Power']


    df_flexible = ""
    if (remove_flex_cons):
      df_flexible = self.remove_flexible_consumption()
      #showNetloadGraph(finalPath + '/netload.csv')


    community_after = pd.read_csv(final_path + '/community.csv', sep=';')  # Header=None to indicate that the first row is data and not colummn names
    community_after.columns = ['Date', 'Power']

    netload_after = pd.read_csv(final_path + '/netload.csv', sep=';')  # Header=None to indicate that the first row is data and not colummn names
    netload_after.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload']


    # Reset community consumption
    #community_after['Power'] = 0
    #netload_after['Demand'] = 0


    placed_appliances = []
    placed_houses = []
    placed_timeslots_array = []


    for timeslot in placed_timeslots:

      timeslot = timeslot.split("-")
      first_item_date = str(int(timeslot[5])-1)
      timeslot_number = int(float(timeslot[0]))
      timeslot_sub_item_number = int(float(timeslot[1]))
      timeslot_power = float(timeslot[2])
      timeslot_first_bin = str(int(timeslot[3]) - 1) # bin 1 corresponds to midnight, bin 2 corresponds to 1 am, etc
      timeslot_number_of_bins = timeslot[4]
      timeslot_last_bin = str(int(float(first_item_date)) + (int(float(timeslot_number_of_bins)) - 1))
      timeslot_bin_before_opt = str(int(float(timeslot[7])) - 1)


      # Gets all the fields of the timeslot (Start, End, Appliance, House, etc)
      timeslot_obj = all_timeslots_objects[timeslot_number]  # If a timeslot is placed, all the subitemms are placed

      # each house consumption profile
      # total_before = pd.read_csv('output/minute/house' + str(timeslotObj["House"]) + '/total.csv', sep=';')
      # total_before.columns = ['Date', 'Power']

      total_after = pd.read_csv(final_path + '/house' + str(timeslot_obj["House"]) + '/total.csv', sep=';')
      total_after.columns = ['Date', 'Power']

      # Reset all houses consumption
      #if (str(timeslot_obj["House"]) not in placed_houses):
      #total_after['Power'] = 0
      #placed_houses.append(str(timeslot_obj["House"]))

      # each appliance consumption profile (of a specific house)
      df_before = pd.read_csv(self.path_steps_minutes + '/house' + str(timeslot_obj["House"]) + '/' + timeslot_obj["Appliance"] + ".csv", sep=';')  # Header=None to indicate that the first row is data and not colummn names
      df_before.columns = ['Date', 'Power']

      df_after = pd.read_csv(final_path + '/house' + str(timeslot_obj["House"]) + '/' + timeslot_obj["Appliance"] + ".csv", sep=';')  # Header=None to indicate that the first row is data and not colummn names
      df_after.columns = ['Date', 'Power']

      # Reset all appliance consumption
      #if ((str(timeslot_obj["House"]) + "-" + str(timeslot_obj["Appliance"])) not in placed_appliances):
      #dfAfter['Power'] = 0
      #placed_appliances.append(str(timeslot_obj["House"]) + "-" + str(timeslot_obj["Appliance"]))

      # when there's more than one item of a timeslot:
      # 1) if its the first hour - starts at the first minutes of the timeslot and ends at 59 miutes
      # 2) if its a middle hour (not the first and not the last) - starts at 00 minutes and ends at 59 minutes
      # 3) if its the last hour - starts at 00 and ends at the last minutes of the timeslot
      # e.g. timeslot from 8.53 to 10.15:
      # hour 8 (bin 9) -> 08:53 (original) - 08:59 (first)
      # hour 9 (bin 10) -> 09:00 - 09:59 (middle)
      # hour 10 (bin 11) -> 10:00 - 10:15 (original) (last)

      tim_new_hour = int(math.floor(int(timeslot_first_bin)/n_bins_per_hour))
      tim_new_min = int((int(timeslot_first_bin)%n_bins_per_hour)*fact)
      tim_old_hour = int(math.floor(int(timeslot_bin_before_opt)/n_bins_per_hour))
      tim_old_min = int((int(timeslot_bin_before_opt) % n_bins_per_hour) * fact)


      if (int(timeslot_number_of_bins) > 1):
        if (int(first_item_date) == int(timeslot_first_bin)):

          timeslot_start_date = str(timeslot_obj["Start"])
          timeslot_end_date = str(timeslot_obj["Start"])[0:11] + str(tim_old_hour).zfill(2) + ":" + str(tim_old_min + (fact - 1)).zfill(2) + ":00"
          new_optimization_start_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(int(tim_new_min+(fact-1)) - (int(tim_old_min+(fact-1))-int(timeslot_obj["Start"][14:16]))).zfill(2) + ":00"
          new_optimization_end_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(tim_new_min + (fact - 1)).zfill(2) + ":00"

        elif (int(timeslot_first_bin) == int(timeslot_last_bin)):

          timeslot_start_date = str(timeslot_obj["Start"])[0:11] + str(tim_old_hour).zfill(2) + ":" + str(tim_old_min).zfill(2) + ":00"
          timeslot_end_date = str(timeslot_obj["End"])
          new_optimization_start_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(tim_new_min).zfill(2) + ":00"
          new_optimization_end_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(int(tim_new_min) + (int(timeslot_obj["End"][14:16])-int(tim_old_min))).zfill(2) + ":00"

        else:

          timeslot_start_date = str(timeslot_obj["Start"])[0:11] + str(tim_old_hour).zfill(2) + ":" + str(tim_old_min).zfill(2) + ":00"
          timeslot_end_date = str(timeslot_obj["Start"])[0:11] + str(tim_old_hour).zfill(2) + ":" + str(tim_old_min + (fact - 1)).zfill(2) + ":00"
          new_optimization_start_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(tim_new_min).zfill(2) + ":00"
          new_optimization_end_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(tim_new_min + (fact - 1)).zfill(2) + ":00"

      else:

        timeslot_start_date = str(timeslot_obj["Start"])
        timeslot_end_date = str(timeslot_obj["End"])
        new_optimization_start_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(int(tim_new_min + (fact - 1)) - (int(tim_old_min + (fact - 1)) - int(timeslot_obj["Start"][14:16]))).zfill(2) + ":00"
        new_optimization_end_date = str(timeslot_obj["Start"])[0:11] + str(tim_new_hour).zfill(2) + ":" + str(int(tim_new_min) + (int(timeslot_obj["End"][14:16]) - int(tim_old_min))).zfill(2) + ":00"


      # list of placed timeslots
      placed_timeslots_array.append(str(timeslot_obj["House"]) + "*" + str(timeslot_obj["Appliance"]) + "*" + str(timeslot_number) + "*" + str(new_optimization_start_date) + "*" + str(new_optimization_end_date))


      # before optimization (original)
      start_obj_before = datetime.datetime.strptime(timeslot_start_date, '%Y-%m-%d %H:%M:%S')  # Convert string to datetime object
      end_obj_before = datetime.datetime.strptime(timeslot_end_date, '%Y-%m-%d %H:%M:%S')  # Convert string to datetime object
      obj_before = start_obj_before

      # after optimization
      start_obj_after = datetime.datetime.strptime(new_optimization_start_date, '%Y-%m-%d %H:%M:%S')  # Convert string to datetime object
      end_obj_after = datetime.datetime.strptime(new_optimization_end_date, '%Y-%m-%d %H:%M:%S')  # Convert string to datetime object
      obj_after = start_obj_after


      while (obj_after != end_obj_after + datetime.timedelta(minutes=1)):


        index_netload_after = netload_after[netload_after.Date == str(obj_after)].index  # Get index of the row
        index_after = community_after[community_after.Date == str(obj_after)].index  # Get index of the row
        index_total_after = total_after[total_after.Date == str(obj_after)].index  # sGet index of the row
        index_app_after = df_after[df_after.Date == str(obj_after)].index  # Get index of the row

        netload_after.loc[index_netload_after, 'Demand'] = float(netload_after[netload_after.Date == str(obj_after)]["Demand"]) + float(df_before[df_before.Date == str(obj_before)]["Power"])  # Subtract the energy of that timeslot from the community energy
        netload_after.loc[netload_after['Production'] < 0, 'Production'] = 0


        community_after.loc[index_after, 'Power'] = float(community_after[community_after.Date == str(obj_after)]["Power"]) + float(df_before[df_before.Date == str(obj_before)]["Power"])  # Subtract the energy of that timeslot from the community energy

        total_after.loc[index_total_after, 'Power'] = float(total_after[total_after.Date == str(obj_after)]["Power"]) + float(df_before[df_before.Date == str(obj_before)]["Power"])  # Subtract the energy of that timeslot from the total energy of that house (the house which corresponds the timeslot)
        df_after.loc[index_app_after, 'Power'] = float(df_after[df_after.Date == str(obj_after)]["Power"]) + float(df_before[df_before.Date == str(obj_before)]["Power"])  # Subtract the energy of that timeslot from the total energy of that house (the house which corresponds the timeslot)

        obj_before = obj_before + datetime.timedelta(minutes=1)  # Next minute
        obj_after = obj_after + datetime.timedelta(minutes=1)  # Next minute


      # After while - when the consumption profile is updated for each minute of the timeslot
      output_directory = os.path.join('', final_path + '/house' + str(timeslot_obj["House"]))
      outname = os.path.join(output_directory, str(timeslot_obj["Appliance"]) + '.csv')
      df_after.to_csv(outname, columns=['Date', 'Power'], sep=";", index=False)

      # After all timeslots updated - update the total of each house
      output_directory = os.path.join('', final_path + '/house' + str(timeslot_obj["House"]))
      outname = os.path.join(output_directory, 'total.csv')
      df_after.to_csv(outname, columns=['Date', 'Power'], sep=";", index=False)

    netload_after["Netload"] = netload_after["Demand"] - netload_after["Production"]

    # After all timeslots updated - update the community profile
    output_directory = os.path.join('', final_path)
    outname = os.path.join(output_directory, 'community.csv')
    community_after.to_csv(outname, columns=['Date', 'Power'], sep=";", index=False)

    # After all timeslots updated - update the community profile
    outname = os.path.join(output_directory, 'netload.csv')
    netload_after.to_csv(outname, columns=['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload'], sep=";", index=False)


    return [placed_timeslots_array, df_flexible]



  def prepare_inputs(self, fact, save_to_file = False, import_prices_hour = [], export_prices_hour = []):
    """
    Prepares the inputs for the optimization problem.
    :return:
    """

    netload = pd.read_csv(self.path_steps_minutes + '/netload.csv',
                          sep=';')  # Header=None to indicate that the first row is data and not colummn names
    netload.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload']

    # Plotd
    # netload.plot(x="Date", y=["Demand", "Production", "Netload"], kind="line", figsize=(10, 10))
    # plt.show()

    fd = str(netload.iloc[0]["Date"])[0:10]
    bins_capacities = []
    bins_maximum = []
    bins_export_prices = []
    bins_import_prices = []
    houses_production = []
    n_bins_per_hour = int(60 / fact)

    # Default values (one value per bin - depends on the number of bins of the day)
    if (len(import_prices_hour) != 24*n_bins_per_hour):
      print("There are no enough import prices for each bin. Default values will be used.")
      import_prices_hour = [0.0] * 24*n_bins_per_hour
    if (len(export_prices_hour) != 24*n_bins_per_hour):
      print("There are no enough export prices for each bin. Default values will be used.")
      export_prices_hour = [0.0] * 24*n_bins_per_hour

    for z in range(0, 24):
      startMin = 0
      endMin = fact - 1
      for w in range(0, n_bins_per_hour):

        tmp_prod = []

        for index, house in enumerate(self.cg.get_community()):
          prod = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/energy.csv', sep=';')
          prod.columns = ['Date', 'Power']

          prod_avg = prod[
            (prod['Date'] >= str(fd) + ' ' + str(z).zfill(2) + ':' + str(startMin).zfill(2) + ':00') & (
                    netload['Date'] <= str(fd) + ' ' + str(z).zfill(2) + ':' + str(endMin).zfill(2) + ':00')][
            'Power'].mean()
          tmp_prod.append(prod_avg)
        houses_production.append(tmp_prod)


        avg = netload[
          (netload['Date'] >= str(fd) + ' ' + str(z).zfill(2) + ':' + str(startMin).zfill(2) + ':00') & (
                  netload['Date'] <= str(fd) + ' ' + str(z).zfill(2) + ':' + str(endMin).zfill(2) + ':00')][
          'Production'].mean()
        max = netload[
          (netload['Date'] >= str(fd) + ' ' + str(z).zfill(2) + ':' + str(startMin).zfill(2) + ':00') & (
                  netload['Date'] <= str(fd) + ' ' + str(z).zfill(2) + ':' + str(endMin).zfill(2) + ':00')][
          'Production'].max()
        bins_capacities.append(avg)
        #bins_capacities.append(avg+5000)
        bins_maximum.append(max)
        bins_export_prices.append(export_prices_hour[z])
        bins_import_prices.append(import_prices_hour[z])

        startMin = startMin + fact
        endMin = endMin + fact

    self.timeslots = self.cg.get_timeslots(self.cg.get_community(), True)

    community = self.cg.get_community()
    appliances_flexibility = {"DISHWASHER": 12, "VACUUMCLEANER": 8, "WASHINGMACHINE": 10, "DRYER": 5, "IRON": 5,
                              "COOKINGSTOVE": 1}
    # appliances_flexibility = {"DISHWASHER": 12, "VACUUMCLEANER": 12, "WASHINGMACHINE": 12, "DRYER": 12, "IRON": 12, "COOKINGSTOVE": 12}
    flexibilities_array = self.cg.get_community_flexibility(community)
    contracted_power = self.cg.calculate_contracted_power(community)


    house_items = [ [] for i in range(len(community))]
    house_items_max = [ [] for i in range(len(community))]
    house_items_date = [ [] for i in range(len(community))]
    house_items_num = [ [] for i in range(len(community))]
    house_items_flex = [ [] for i in range(len(community))]

    house_s_soc = [ [] for i in range(len(community))]
    house_s_min = [ [] for i in range(len(community))]
    house_s_max = [ [] for i in range(len(community))]


    if (save_to_file):

      dates = []
      items = []
      items_max = []
      timeslot_numbers = []
      count = 0
      flexibilities = []

      print("Timeslots List")
      for timeslot in self.timeslots:

        print(timeslot)

        # Fill timeslots (with subitems) array
        df = pd.read_csv(self.path_steps_minutes + '/house' + str(timeslot['House']) + '/' + timeslot['Appliance'] + ".csv",
                         sep=';')  # Header=None to indicate that the first row is data and not colummn names
        df.columns = ['Date', 'Power']
        df = df[:24 * 60 * 60]  # Only the first day is important (24 hours * 60 minutes * 60 seconds)
        # df = df.fillna(0) # fills nan with 0

        # Fill dates array
        start_hour = int(str(timeslot['Start'])[11:13])
        end_hour = int(str(timeslot['End'])[11:13])
        start_date = str(timeslot['Start'])[0:10]
        start_minute = int(str(timeslot['Start'])[14:16])
        end_minute = int(str(timeslot['End'])[14:16])

        hour = start_hour
        temp_date = []
        temp_tim = []
        temp_num = []
        temp_max = []
        temp_flex = []

        while (hour <= end_hour):

          for w in range(0, n_bins_per_hour):

            if (n_bins_per_hour > 1):
              # for example, if we have bins of 30 minutes and the startMinute is 30 or higher, then we just have the second bin of that hour
              if (w != n_bins_per_hour - 1 and hour == start_hour and start_minute >= fact * (w + 1)):
                continue

              if (hour == end_hour and end_minute < fact * w):
                continue

            if (hour == start_hour and start_minute < fact * (w + 1) and start_minute >= fact * w):
              start = start_minute
            else:
              start = w * fact

            if (hour == end_hour and fact * (w + 1) >= end_minute):
              end = end_minute
            elif (hour == start_hour and w == 0):
              end = fact - 1
            else:
              end = (w + 1) * fact - 1

            duration_in_minutes = end - start + 1
            tim = (df[(df['Date'] >= str(start_date) + ' ' + str(hour).zfill(2) + ':' + str(start).zfill(2) + ':00') & (
                    df['Date'] <= str(start_date) + ' ' + str(hour).zfill(2) + ':' + str(end).zfill(2) + ':00')][
                     'Power'].mean()) * (duration_in_minutes / 60)
            max = df[(df['Date'] >= str(start_date) + ' ' + str(hour).zfill(2) + ':' + str(start).zfill(2) + ':00') & (
                    df['Date'] <= str(start_date) + ' ' + str(hour).zfill(2) + ':' + str(end).zfill(2) + ':00')][
              'Power'].max()

            temp_date.append((hour * n_bins_per_hour) + w + 1)  # 10 am corresponds to bin 11
            temp_tim.append(tim)
            temp_max.append(max)
            temp_num.append(count)
            temp_flex.append(flexibilities_array[int(timeslot['House'])] * appliances_flexibility[timeslot['Appliance']])

          hour = hour + 1

        # Individual houses inputs
        house_items[int(timeslot["House"])].append(temp_tim)
        house_items_max[int(timeslot["House"])].append(temp_max)
        house_items_date[int(timeslot["House"])].append(temp_date)
        house_items_num[int(timeslot["House"])].append(temp_num)
        house_items_flex[int(timeslot["House"])].append(temp_flex)


        dates.append(temp_date)
        items.append(temp_tim)
        items_max.append(temp_max)
        timeslot_numbers.append(temp_num)
        flexibilities.append(temp_flex)
        count = count + 1


      df = pd.DataFrame(flexibilities)
      df.to_csv('inputs/flexibilities.csv', index=False)

      df = pd.DataFrame(dates)
      df.to_csv('inputs/dates.csv', index=False)

      df = pd.DataFrame(items)
      df.to_csv('inputs/items.csv', index=False)

      df = pd.DataFrame(items_max)
      df.to_csv('inputs/items_max.csv', index=False)

      df = pd.DataFrame(timeslot_numbers)
      df.to_csv('inputs/timeslot_numbers.csv', index=False)

      df = pd.DataFrame(houses_production)
      df.to_csv('inputs/houses_production.csv', index=False)

      for index, house in enumerate(community):

        df = pd.DataFrame(house_items[index])
        df.to_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items.csv', index=False)

        df = pd.DataFrame(house_items_max[index])
        df.to_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_max.csv', index=False)

        df = pd.DataFrame(house_items_date[index])
        df.to_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_date.csv', index=False)

        df = pd.DataFrame(house_items_num[index])
        df.to_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_num.csv', index=False)

        df = pd.DataFrame(house_items_flex[index])
        df.to_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_flex.csv', index=False)

    else:

      flexibilities = pd.read_csv('inputs/flexibilities.csv')
      flexibilities = flexibilities.to_numpy()
      flexibilities = [[x for x in y if not np.isnan(x)] for y in flexibilities]

      dates = pd.read_csv('inputs/dates.csv')
      dates = dates.to_numpy()
      dates = [[x for x in y if not np.isnan(x)] for y in dates]

      items = pd.read_csv('inputs/items.csv')
      items = items.to_numpy()
      items = [[x for x in y if not np.isnan(x)] for y in items]

      items_max = pd.read_csv('inputs/items_max.csv')
      items_max = items_max.to_numpy()
      items_max = [[x for x in y if not np.isnan(x)] for y in items_max]

      timeslot_numbers = pd.read_csv('inputs/timeslot_numbers.csv')
      timeslot_numbers = timeslot_numbers.to_numpy()
      timeslot_numbers = [[x for x in y if not np.isnan(x)] for y in timeslot_numbers]

      houses_production = pd.read_csv('inputs/houses_production.csv')
      houses_production = houses_production.to_numpy()
      houses_production = [[x for x in y if not np.isnan(x)] for y in houses_production]

      for index, house in enumerate(community):

        try:
          df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items.csv')
          house_items[index] = df.to_numpy()
          house_items[index] = [[x for x in y if not np.isnan(x)] for y in house_items[index]]
        except:
          house_items[index] = []

        try:
          df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_max.csv')
          house_items_max[index] = df.to_numpy()
          house_items_max[index] = [[x for x in y if not np.isnan(x)] for y in house_items_max[index]]
        except:
          house_items_max[index] = []

        try:
          df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_date.csv')
          house_items_date[index] = df.to_numpy()
          house_items_date[index] = [[x for x in y if not np.isnan(x)] for y in house_items_date[index]]
        except:
          house_items_date[index] = []

        try:
          df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_num.csv')
          house_items_num[index] = df.to_numpy()
          house_items_num[index] = [[x for x in y if not np.isnan(x)] for y in house_items_num[index]]
        except:
          house_items_num[index] = []

        try:
          df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_items_flex.csv')
          house_items_flex[index] = df.to_numpy()
          house_items_flex[index] = [[x for x in y if not np.isnan(x)] for y in house_items_flex[index]]
        except:
          house_items_flex[index] = []


    for index, house in enumerate(community):

      df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_s.csv', sep=";")
      house_s_soc[index] = df.to_numpy()[:,0] * 1000
      house_s_soc[index] = [x for x in house_s_soc[index]]

      df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_s.csv', sep=";")
      house_s_min[index] = df.to_numpy()[:,1] * 1000
      house_s_min[index] = [x for x in house_s_min[index]]

      df = pd.read_csv(self.path_steps_minutes + '/house' + str(index) + '/house_s.csv', sep=";")
      house_s_max[index] = df.to_numpy()[:,2] * 1000
      house_s_max[index] = [x for x in house_s_max[index]]


    num_houses = len(community)

    # Storage Inputs
    storage_df = pd.read_csv('inputs/s_inputs.csv')
    s_initial_soc = storage_df.to_numpy()[:,0] * 1000
    s_min = storage_df.to_numpy()[:,1] * 1000
    s_max = storage_df.to_numpy()[:,2] * 1000


    print("Community Flexibilities:")
    print(flexibilities)
    print("Bin Capacities:")
    print(bins_capacities)
    print("Bin Maximum:")
    print(bins_maximum)
    print("Dates:")
    print(dates)
    print("Timeslots:")
    print(items)
    print("Timeslots Maximum:")
    print(items_max)
    print("Numbers:")
    print(timeslot_numbers)
    print("Storage Max")
    print(s_max)
    print("Storage Min")
    print(s_min)
    print("Storage Initial SOC")
    print(s_initial_soc)
    print("Houses Production:")
    print(houses_production)
    print("Export Price:")
    print(bins_export_prices)
    print("Import Price:")
    print(bins_import_prices)
    print("Timeslots (Individual):")
    print(house_items)
    print("Timeslots Maximum (Individual):")
    print(house_items_max)
    print("Dates (Individual):")
    print(house_items_date)
    print("Numbers (Individual):")
    print(house_items_num)
    print("Flexibilities (Individual):")
    print(house_items_flex)
    print("S SOC (Individual):")
    print(house_s_soc)
    print("S Max (Individual):")
    print(house_s_max)
    print("S Min (Individual):")
    print(house_s_min)

    res = Input(contracted_power, fd, dates, items, bins_capacities, timeslot_numbers, bins_maximum, items_max, n_bins_per_hour, flexibilities, bins_export_prices, bins_import_prices, s_max, s_min, s_initial_soc, num_houses, houses_production, house_items, house_items_max, house_items_date, house_items_num, house_items_flex, house_s_soc, house_s_max, house_s_min)
    return res



  @abstractmethod
  def execute(self, *args):
    """
    This function should be implemented in a class which inherits from this one.
    This goal is to define all the steps necessary to implement the provided strategy which will allow to do a good management of the renewable resources of the community.

    Args:
      args: can have as many arguments as you want
    """
    pass

