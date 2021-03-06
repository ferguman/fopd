from sys import exc_info

from flask import Flask, render_template, __version__, make_response

from python.logger import get_sub_logger 

class fopdwFlask(Flask):

    jinja_options = Flask.jinja_options.copy()

    # change the server side Jinja template code markers so that we can use Vue.js on the client.
    # Vue.js uses {{ }} as code markers so we don't want Jinja to interpret them.
    jinja_options.update(dict(
        block_start_string = '(%',
        block_end_string = '%)',
        variable_start_string = '((',
        variable_end_string = '))',
        comment_start_string = '(#',
        comment_end_string = '#)',
    ))

logger = get_sub_logger(__name__)

def start(app_state, args, barrier):

    '''
    args is a dictionary.  The following arg values are supported:

    chart_list_source: If there is a resource that can create chart files then use the
                       the name here (e.g. 'chart_list_source':'wc'). If there
                       are no charts available on this fopd then set this value to None
                       (e.g. 'chart_list_source':None)
    '''

    #TODO - add authentication to the application.

    logger.info('starting Flask version {}'.format(__version__))

    app = fopdwFlask(__name__)

    @app.route('/')
    def home():

        if args['chart_list_source']:
            cl = app_state[args['chart_list_source']]['chart_list']
        else:
            cl = [] 
        resp = make_response(render_template('home.html', 
                                             chart_list=cl, num_of_charts=len(cl)))

        resp.headers['Cache-Control'] = 'max-age:0, must-revalidate'
        return resp

    @app.route('/config.html')
    def config():
        return make_response(render_template('config.html'))

    
    @app.route('/v1/mqtt_status')
    def mqtt_status():
        return make_response(app_state['mqtt']['status']())


    # Let the system know that you are good to go.
    try:
        barrier.wait()
    except Exception as err:
        # assume a broken barrier
        logger.error('barrier error: {}'.format(str(err)))
        app_state['stop'] = True

    # Start the Flask application. Note: app.run does not return.
    if not app_state['stop']:

        try:
           app.run(host=args['host'], port=args['port'])
        except:
           logger.error('Local web server has crashed: {}'.format(exc_info()[0], exc_info()[1]))


        logger.error('fopd will continue running, however the local webserver has stoppped')
