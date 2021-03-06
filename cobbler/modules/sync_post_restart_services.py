import distutils.sysconfig
import sys
import os
import traceback
import cexceptions
import os
import sys
import xmlrpclib
import cobbler.module_loader as module_loader
import cobbler.utils as utils

plib = distutils.sysconfig.get_python_lib()
mod_path="%s/cobbler" % plib
sys.path.insert(0, mod_path)

def register():
    # this pure python trigger acts as if it were a legacy shell-trigger, but is much faster.
    # the return of this method indicates the trigger type
    return "/var/lib/cobbler/triggers/sync/post/*"

def run(api,args,logger):

    settings = api.settings()

    manage_dhcp        = str(settings.manage_dhcp).lower()
    manage_dns         = str(settings.manage_dns).lower()
    restart_bin        = str(settings.restart_bin).lower()
    restart_dhcp       = str(settings.restart_dhcp).lower()
    restart_dns        = str(settings.restart_dns).lower()
    dhcpd_bin          = str(settings.dhcpd_bin).lower()
    dhcpd_init         = str(settings.dhcpd_init).lower()
    omapi_enabled      = str(settings.omapi_enabled).lower()
    omapi_port         = str(settings.omapi_port).lower()

    which_dhcp_module = module_loader.get_module_from_file("dhcp","module",just_name=True).strip()
    which_dns_module  = module_loader.get_module_from_file("dns","module",just_name=True).strip()

    # special handling as we don't want to restart it twice
    has_restarted_dnsmasq = False

    rc = 0
    if manage_dhcp != "0":
        if which_dhcp_module == "manage_isc":
            if not omapi_enabled in [ "1", "true", "yes", "y" ] and restart_dhcp:
                rc = utils.subprocess_call(logger, "%s -t -q" % dhcpd_bin, shell=True)
                if rc != 0:
                   logger.error("%s -t failed" % dhcpd_bin)
                   return 1
                rc = utils.subprocess_call(logger,"%s %s restart" % (restart_bin, dhcpd_init), shell=True)
        elif which_dhcp_module == "manage_dnsmasq":
            if restart_dhcp:
                rc = utils.subprocess_call(logger, "/sbin/service dnsmasq restart")
                has_restarted_dnsmasq = True
        else:
            logger.error("unknown DHCP engine: %s" % which_dhcp_module)
            rc = 411

    if manage_dns != "0" and restart_dns != "0":
        if which_dns_module == "manage_bind":
            rc = utils.subprocess_call(logger, "/sbin/service named restart", shell=True)
        elif which_dns_module == "manage_dnsmasq" and not has_restarted_dnsmasq:
            rc = utils.subprocess_call(logger, "/sbin/service dnsmasq restart", shell=True)
        elif which_dns_module == "manage_dnsmasq" and has_restarted_dnsmasq:
            rc = 0
        else:
            logger.error("unknown DNS engine: %s" % which_dns_module)
            rc = 412

    return rc

