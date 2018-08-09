# Food Computer Version 1 Data Logger
#
# Reads the following app_state variables
#   stop
#   sensor_readings
#   mqtt
#
#  No app_state variables are written.
#

from time import sleep, time
from logging import getLogger
from python.send_mqtt_data import send_sensor_data_via_mqtt_v2

logger = getLogger('mvp.' + __name__)

def time_to_sample(interval, state):

   if interval <= 0 or interval > 86400:
      logger.error('The data_logger_sample_interval must be '
                 + 'set to a value between 1 and 86400. BTW: 86400 seconds is 24 hours.')
      return False

   if state['next_sample_time'] <= time():
      state['next_sample_time'] = time() + interval 
      return True
   else:
      return False
    
def start(app_state, args, b):
   
    logger.setLevel(args['log_level'])
    logger.info('starting data logger')

    # Set state so that a sample is taken on startup.
    state = {'next_sample_time':0}
    
    # Don't proceed till the sensor logger and mqtt threads are up and running. Otherwise you 
    # won't have any sensor readings to log or any mqtt to send them.
    b.wait()    

    while not app_state['stop']:

       if time_to_sample(args['sample_interval'], state):

            logger.info('Logging sensor readings')

            if 'sensor_readings' in app_state:
                for r in app_state['sensor_readings']:

                    # check for empty values - don't log them. Warn somebody about it.
                    if r['value'] is None:
                        logger.warning('Empyt value for {} {}'.format(r['subject'], r['attribute']))
                        continue 
                    if r['ts'] is None:
                        logger.warning('Empty time stamp for {} {}'.format(r['subject'], r['attribute']))
                        continue

                    #Log the value remotely.
                    if args['log_data_via_mqtt'] and ('mqtt' in app_state):
                        #TBD: Need to make sure this statement completes before other threads get a wack
                        #     at the processor.
                        send_sensor_data_via_mqtt_v2(r, app_state['mqtt'])
                    elif not ('mqtt' in app_state):
                        logger.warning('no mqtt client avaiable.')
            else:
                logger.error('no sensor readings available.')
      
       sleep(1)