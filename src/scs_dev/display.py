#!/usr/bin/env python3

"""
Created on 23 Jun 2019

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

DESCRIPTION
The display utility is used to set the content for a visual display, such as the Pimoroni Inky pHAT eInk module.
Content is gained from several sources:

* The display_conf settings
* System status
* Input from stdin or a Unix domain socket
* MQTT client and GPS receiver report files (if available)

SYNOPSIS
display.py [-u UDS] [-v]

EXAMPLES
/home/pi/SCS/scs_dev/src/scs_dev/display.py -v -u /home/pi/SCS/pipes/display.uds

SEE ALSO
scs_mfr/display_conf
scs_mfr/gps_conf
scs_mfr/mqtt_conf

RESOURCES
sudo apt install libatlas3-base
sudo apt-get install libopenjp2-7
"""

from scs_core.comms.mqtt_conf import MQTTConf
from scs_core.comms.uds_reader import UDSReader

from scs_core.sys.logging import Logging
from scs_core.sys.signalled_exit import SignalledExit

from scs_dev.cmd.cmd_display import CmdDisplay

from scs_dfe.gps.gps_conf import GPSConf
from scs_dfe.interface.interface_conf import InterfaceConf

from scs_display.display.display_conf import DisplayConf

from scs_host.bus.i2c import I2C
from scs_host.comms.domain_socket import DomainSocket
from scs_host.sys.host import Host

from scs_psu.psu.psu_conf import PSUConf


# --------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    conf = None
    interface = None
    monitor = None

    # ------------------------------------------------------------------------------------------------------------
    # cmd...

    cmd = CmdDisplay()

    # logging...
    Logging.config('display', verbose=cmd.verbose)
    logger = Logging.getLogger()

    logger.info(cmd)

    try:
        I2C.Utilities.open()

        # ------------------------------------------------------------------------------------------------------------
        # resources...

        # software update...
        software_report = Host.software_update_report()

        # PSUConf...
        psu_conf = PSUConf.load(Host)
        psu_report_filename = None if psu_conf is None else psu_conf.report_file(Host)
        psu_report_class = None if psu_conf is None else psu_conf.psu_report_class()

        # MQTTConf...
        mqtt_conf = MQTTConf.load(Host)
        queue_report_filename = None if mqtt_conf is None else mqtt_conf.report_file(Host)

        # GPSConf...
        gps_conf = GPSConf.load(Host)
        gps_report_filename = None if gps_conf is None else gps_conf.report_file(Host)

        # UDSReader...
        reader = UDSReader(DomainSocket, cmd.uds)

        if cmd.uds:
            logger.info(reader)

        # Interface...
        interface_conf = InterfaceConf.load(Host)
        interface = None if interface_conf is None else interface_conf.interface()

        if interface:
            logger.info(interface)

        # DisplayConf...
        try:
            conf = DisplayConf.load(Host)

            if conf is None:
                logger.error("DisplayConf not set.")
                exit(1)

        except NotImplementedError:
            logger.error("not available.")
            exit(1)

        monitor = conf.monitor(software_report, psu_report_class, psu_report_filename, queue_report_filename,
                               gps_report_filename)

        if monitor:
            logger.info(monitor)


        # ------------------------------------------------------------------------------------------------------------
        # run...

        if interface:
            interface.power_opc(True)                       # otherwise the SPI bus is held low

        # signal handler...
        SignalledExit.construct()

        monitor.start()

        reader.connect()

        for message in reader.messages():
            logger.info(message)
            monitor.set_message(message)


    # ----------------------------------------------------------------------------------------------------------------
    # end...

    except ConnectionError as ex:
        logger.error(repr(ex))

    except (KeyboardInterrupt, SystemExit):
        pass

    finally:
        logger.info("finishing")

        if monitor:
            monitor.stop()

        # if interface:
        #     interface.power_opc(False)

        I2C.Utilities.close()
