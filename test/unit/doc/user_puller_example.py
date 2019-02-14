from powerapi import ActorPuller, YYYModel, XXXDB, Filter

# Create the XXXDB object which handle the link to the database
xxxDB = XXXDB(..., report_model=YYYModel())

# Create your customize filter
# Add rule on your filter
# With this configuration, all the data will be send to
# dispatcher1, and never to dispatcher2.
customize_filter = Filter()
customize_filter.filter(lambda msg: True, dispatcher1)
customize_filter.filter(lambda msg: False, dispatcher2)

# Define the frequency that the Puller will use to read in the
# database. 0 mean that it will read as faster as it can.
frequency = 0

# Create the Puller Actor
puller = PullerActor("puller_name", xxxDB, customize_filter, frequency)
