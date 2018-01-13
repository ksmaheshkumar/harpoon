#! /usr/bin/env python
import sys
from dns import resolver, reversename
from harpoon.commands.base import Command
from harpoon.lib.utils import is_ip


class CommandDns(Command):
    """
    # DNS plugin

    **Map DNS information for a domain or an IP address**

    * Check DNS information on a domain: `harpoon dns DOMAIN`
    * Check for all types of DNS entries: `harpoon dns -e DOMAIN`

    """
    # TODO: graph output
    # TODO: option to define DNS server
    name = "dns"
    description = "Map DNS information for a domain or an IP"
    config = {}
    all_types = ['NONE', 'A', 'NS', 'MD', 'MF', 'CNAME', 'SOA', 'MB', 'MG',
        'MR', 'NULL', 'WKS', 'PTR', 'HINFO', 'MINFO', 'MX', 'TXT', 'RP',
        'AFSDB', 'X25', 'ISDN', 'RT', 'NSAP', 'NSAP-PTR', 'SIG', 'KEY',
        'PX', 'GPOS', 'AAAA', 'LOC', 'NXT', 'SRV', 'NAPTR', 'KX', 'CERT',
        'A6', 'DNAME', 'OPT', 'APL', 'DS', 'SSHFP', 'IPSECKEY', 'RRSIG',
        'NSEC', 'DNSKEY', 'DHCID', 'NSEC3', 'NSEC3PARAM', 'TLSA', 'HIP',
        'CDS', 'CDNSKEY', 'CSYNC', 'SPF', 'UNSPEC', 'EUI48', 'EUI64',
        'TKEY', 'TSIG', 'IXFR', 'AXFR', 'MAILB', 'MAILA', 'ANY', 'URI',
        'CAA', 'TA', 'DLV']

    def add_arguments(self, parser):
        parser.add_argument('TARGET', help='Domain or IP to query')
        parser.add_argument('--extended', '-e', action='store_true',
                help="Extended testing of all DNS types")
        self.parser = parser

    def owner_to_email(self, owner):
        rev = owner[:-1].split('.')
        return '.'.join(rev[:-2]) + "@" + ".".join(rev[-2:])

    def run(self, conf, args, plugins):
        if is_ip(args.TARGET):
            # That's an IP address
            ptr_n = str(reversename.from_address(args.TARGET))
            try:
                answer = [entry for entry in resolver.query(ptr_n, "PTR")][0]
                print("%s - %s" % (ptr_n, str(answer)))
            except resolver.NXDOMAIN:
                print("%s - %s" % (ptr_n, "NXDOMAIN"))
        else:
            cip = plugins['ip']
            if args.extended:
                for a in self.all_types:
                    try:
                        answers = resolver.query(args.TARGET, a)
                        for rdata in answers:
                            print(a, ':', rdata.to_text())
                    except Exception as e:
                        pass
            else:
                # A
                print("# A")
                try:
                    answers = resolver.query(args.TARGET, 'A')
                except resolver.NoAnswer:
                    print("No A entry")
                else:
                    for rdata in answers:
                        info = cip.ipinfo(rdata.address)
                        print("%s: ASN%i %s - %s %s" % (
                                rdata.address,
                                info['asn'],
                                info['asn_name'],
                                info['city'],
                                info['country']
                            )
                        )

                # AA
                print("")
                print("# AAAA")
                try:
                    answers = resolver.query(args.TARGET, 'AAAA')
                    for rdata in answers:
                        print(rdata.address)
                except resolver.NoAnswer:
                    print("No AAAA entry configured")

                # DNS Servers
                print("\n# NS")
                try:
                    answers = resolver.query(args.TARGET, 'NS')
                except resolver.NoAnswer:
                    # That's pretty unlikely
                    print("No NS entry configured")
                else:
                    for entry in answers:
                        target = str(entry.target)
                        if is_ip(target):
                            # Pretty unlikely
                            info = cip.ipinfo(target)
                            print("%s - ASN%i %s - %s %s" % (
                                    target,
                                    info['asn'],
                                    info['asn_name'],
                                    info['city'],
                                    info['country']
                                )
                            )
                        else:
                            try:
                                ip = [b.address for b in resolver.query(target, 'A')][0]
                            except resolver.NoAnswer:
                                # Hostname without IPv4
                                print(target)
                            else:
                                # Hostname
                                info = cip.ipinfo(ip)
                                print("%s - %s - ASN%i %s - %s %s" % (
                                        target,
                                        ip,
                                        info['asn'],
                                        info['asn_name'],
                                        info['city'],
                                        info['country']
                                    )
                                )

                # MX
                print("\n# MX:")
                try:
                    answers = resolver.query(args.TARGET, 'MX')
                except resolver.NoAnswer:
                    print("No MX entry configured")
                else:
                    for rdata in answers:
                        if is_ip(rdata.exchange):
                            # IP directly
                            info = cip.ipinfo(rdata.exchange)
                            print("%i %s - ASN%i %s - %s %s" % (
                                    rdata.preference,
                                    rdata.exchange,
                                    info['asn'],
                                    info['asn_name'],
                                    info['city'],
                                    info['country']
                                )
                            )
                        else:
                            try:
                                ip = [b.address for b in resolver.query(rdata.exchange, 'A')][0]
                            except resolver.NoAnswer:
                                # Hostname without IPv4
                                print(rdata.exchange)
                            else:
                                # Hostname
                                info = cip.ipinfo(ip)
                                print("%i %s - %s - ASN%i %s - %s %s" % (
                                        rdata.preference,
                                        rdata.exchange,
                                        ip,
                                        info['asn'],
                                        info['asn_name'],
                                        info['city'],
                                        info['country']
                                    )
                                )

                # SOA
                print("\n# SOA")
                try:
                    answers = resolver.query(args.TARGET, 'SOA')
                except resolver.NoAnswer:
                    print("No SOA entry configured")
                else:
                    entry = [b for b in answers][0]
                    print("NS: %s" % str(entry.mname))
                    print("Owner: %s" % self.owner_to_email(str(entry.rname)))

                # TXT
                print("\n# TXT:")
                try:
                    answers = resolver.query(args.TARGET, 'TXT')
                except resolver.NoAnswer:
                    print("No TXT entry configured")
                else:
                    for a in answers:
                        print(a.to_text())
