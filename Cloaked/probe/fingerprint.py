"""
PLEASE DO NOT EDIT THIS FILE IF YOU DON'T KNOW WHAT YOU'RE DOING
THIS FILE IS FULL OF GARBAGE THAT I DON'T EVEN KNOW WHAT I'M DOING
THIS FILE IS CREATED WHEN I'M DRUNK

WILl APPRECIATE IF ANYONE CAN CLEAN THIS PILE OF CODE
"""


import random
import re


class OSFingerprint:

    def __init__(self, file, debug):

        # Main Stuff

        self.debug = debug
        self.probe = dict()

        # Variables
        self.tcp_isn = 0
        self.tcp_gcd = 1
        self.tcp_isn_stdDev = 0
        self.tcp_isn_delta = 0

        self.ip_id = 0
        self.ip_id_delta = 0
        self.ip_id_icmp_delta = None
        self.ip_id_icmp = None

        self.ttl = '0x40'
        self.Craft_Respond = {
            'PKT_1': True,
            'PKT_2': True,
            'PKT_3': True,
            'PKT_4': True,
            'PKT_5': True,
            'PKT_6': True,
            'ECN': True,
            'T2': True,
            'T3': True,
            'T4': True,
            'T5': True,
            'T6': True,
            'T7': True,
            'U1': True,
            'IE': True
        }

        self.parse(file)

    def parse(self, fname):
        pattern_bracket = '(.*?)\\((.*?)\\)'
        try:
            with open(fname, 'r') as f:
                os = f.readlines()
            self.info('DEBUG: OS Fingerprint Is File, Read Complete')
            self.info('DEBUG: ------------------------------------------')
        except (FileNotFoundError, OSError, TypeError):
            os = fname.split('\n')
            self.info('DEBUG: OS Fingerprint Is String, Read Complete')
            self.info('DEBUG: ------------------------------------------')

        for line in os:
            line.strip()
            result = re.search(pattern_bracket, line)

            if result:
                self.probe[result.group(1)] = dict()

                for node in result.group(2).split('%'):
                    key, value = node.split('=')
                    if '|' in value:
                        value = random.choice(value.split('|'))

                    if '-' in value:
                        min_val, max_val = value.split('-')
                        min_val, max_val = self.swapcheck(min_val, max_val)
                        value = random.randint(min_val, max_val)
                        value = hex(value)
                        if key == 'SP':
                            self.probe[result.group(1)]['SP_MIN'] = min_val
                            self.probe[result.group(1)]['SP_MAX'] = max_val
                        if key == 'ISR':
                            self.probe[result.group(1)]['ISR_MIN'] = min_val
                            self.probe[result.group(1)]['ISR_MAX'] = max_val

                    self.probe[result.group(1)][key] = value

        # Check U1 Probe
        self.u1_update()

        # Check IE Probe
        self.ie_update()

        # Check OPS Probe
        self.ops_update()

        # Check ECN Probe
        self.ecn_update()

        # Check T2-T7 Probe
        self.t2tot7_update()

        # Check Sequence Generator [PKT_1 TO PKT_5] Probe
        self.seqgen_update()
        self.t1_update()

        # Check WIN Probe
        self.win_update()

        # Resolve TCP Sequence Value
        self.tcp_seq_init()

        # Resolve IP ID Value
        self.ip_id_init()

        self.info('DEBUG: ------------------------------------------')
        self.info('DEBUG: Finished Parsing OS Fingerprint')

    def ip_id_init(self):
        self.ip_id = 0
        try:
            ti = self.probe['SEQ']['TI']
        except KeyError:
            ti = 'O'

        if ti == 'Z':
            self.ip_id_delta = 0
        elif ti == 'RD':
            self.ip_id_delta = 30000
        elif ti== 'RI':
            self.ip_id_delta = 1234
        elif ti == 'BI':
            self.ip_id_delta = 1024 + 256
        elif ti == 'I':
            self.ip_id_delta = 1
        elif ti == 'O':
            self.ip_id_delta = 123
        else:
            self.ip_id_delta = int(ti, 16)

        try:
            ss = self.probe['SEQ']['SS']
        except KeyError:
            ss = 'O'

        self.ip_id_icmp_delta = None
        if ss == 'S':
            self.ip_id_icmp = None
        else:
            self.ip_id_icmp = 0
            try:
                ii = self.probe['SEQ']['II']
            except KeyError:
                ii = 'O'

            if ii == 'Z':
                self.ip_id_icmp_delta = 0
            elif ii == 'RD':
                self.ip_id_icmp_delta = 30000
            elif ii == 'RI':
                self.ip_id_icmp_delta = 1234
            elif ii == 'BI':
                self.ip_id_icmp_delta = 1024+256
            elif ii == 'I':
                self.ip_id_icmp_delta = 1
            elif ii == 'O':
                self.ip_id_icmp_delta = 123
            else:
                self.ip_id_icmp_delta = int(ii, 16)
        for i in range(10):
            self.ip_id_gen()
            self.ip_id_icmp_gen()

        self.info('DEBUG: IP ID Delta: %d' % self.ip_id_delta)
        self.info('DEBUG: IP ID ICMP Delta: %s' % self.ip_id_icmp_delta)

    def ip_id_gen(self):
        ans = self.ip_id
        self.ip_id += self.ip_id_delta
        self.ip_id %= 0x10000
        return ans

    def ip_id_icmp_gen(self):
        if self.ip_id_icmp is None:
            return self.ip_id_gen()

        ans = self.ip_id_icmp
        self.ip_id_icmp += self.ip_id_icmp_delta
        self.ip_id_icmp %= 0x10000
        return ans

    def tcp_seq_init(self):
        self.tcp_isn = 0
        try:
            self.tcp_gcd = int(self.probe['SEQ']['GCD'], 16)
        except KeyError:
            self.tcp_gcd = 1

        try:
            isr = int(self.probe['SEQ']['ISR'], 16)
        except KeyError:
            isr = 1

        try:
            sp = int(self.probe['SEQ']['SP'], 16)
        except KeyError:
            sp = 1

        self.tcp_isn_stdDev = (2**(sp/8.0)) * 5 / 4

        if self.tcp_gcd > 9:
            self.tcp_isn_stdDev *= self.tcp_gcd

        self.tcp_isn_stdDev *= 0.11
        self.tcp_isn_delta = 2**(isr/8.0) * 0.11
        for i in range(10):
            self.tcp_seq_gen()
        self.info('DEBUG: TCP ISN Delta: %f' % self.tcp_isn_delta)
        self.info('DEBUG: TCP ISN Standard Deviation %f' % self.tcp_isn_stdDev)

    def tcp_seq_gen(self):
        ans = self.tcp_isn + self.tcp_isn_stdDev
        self.tcp_isn_stdDev *= -1
        ans = int(int(ans/self.tcp_gcd) * self.tcp_gcd)
        self.tcp_isn += self.tcp_isn_delta
        self.tcp_isn %= 0x100000000
        return ans % 0x100000000

    def seqgen_update(self):
        if 'SEQ' in self.probe:
            if 'SP' not in self.probe['SEQ'] and 'GCD' not in self.probe['SEQ'] and'ISR' not in self.probe['SEQ']:
                self.probe['SEQ']['SP'] = '0'
                self.probe['SEQ']['GCD'] = '1'
                self.probe['SEQ']['ISR'] = '0'
        else:
            self.probe['SEQ'] = dict()
            # NOT SURE WHICH TO SET AS FALSE TO STOP SEQ
            # self.Craft_respond[''] = False
            return

        # Update SEQ Timestamp
        if 'TS' in self.probe['SEQ']:
            ts = self.probe['SEQ']['TS']

            if ts == 'U':
                new_ts = 1
            elif ts == '0':
                new_ts = 0
            elif ts == '1':
                new_ts = random.randint(0, 5)
            elif ts == '7':
                new_ts = random.randint(70, 150)
            elif ts == '8':
                new_ts = random.randint(150, 350)
            else:
                new_ts = 2048
            self.probe['SEQ']['TS'] = new_ts

        else:
            self.info('DEBUG: TS Value Not Found. Setting TS Value To 2048')
            self.probe['SEQ']['TS'] = 2048

        if 'GCD' in self.probe['SEQ']:
            if self.probe['SEQ']['GCD'] == '0':
                self.probe['SEQ']['GCD'] = '1'

    def t1_update(self):
        if 'T1' in self.probe:
            if 'R' in self.probe['T1']:
                if self.probe['T1']['R'] == 'N':
                    self.Craft_Respond['PKT_1'] = False
        else:
            self.probe['T1'] = dict()
            self.Craft_Respond['PKT_1'] = False

        # Update DF Value
        if 'DF' not in self.probe['T1']:
            self.info('DEBUG_T1: DF Value Not Found. Setting to 0 (N)')
            df_flag = 0
        elif self.probe['T1']['DF'] == 'Y':
            df_flag = 2
        else:
            df_flag = 0
        self.probe['T1']['DF'] = df_flag

        # Update S Value
        if 'S' not in self.probe['T1']:
            self.info('DEBUG_T1: S Value Not Found. Setting to Default (A)')
            s_val = 'A'
            self.probe['T1']['S'] = s_val

        # Update A Value
        if 'A' not in self.probe['T1']:
            self.info('DEBUG_T1: A Value Not Found. Setting to Default (S)')
            a_val = 'S'
            self.probe['T1']['A'] = a_val

        # Update F Value
        if 'F' not in self.probe['T1']:
            self.info('DEBUG_T1: F Value Not Found. Setting to Default (SA)')
            f_val = 'SA'
            self.probe['T1']['F'] = f_val

        # Update RD Value
        if 'RD' not in self.probe['T1']:
            self.info('DEBUG_T1: RD Value Not Found. Setting to 0')
            self.probe['T1']['RD'] = '0'

        # Update TTL and Guess Value (T, TG)
        try:
            ttl_val = self.probe['T1']['T']
        except KeyError:
            self.info('DEBUG_T1: T Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
        self.probe['T1']['TTL'] = ttl_val
        self.ttl = ttl_val

        try:
            ttl_val = self.probe['T1']['TG']
        except KeyError:
            self.info('DEBUG_T1: TG Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
            pass
        self.probe['T1']['TTL'] = ttl_val
        self.ttl = ttl_val

    def t2tot7_update(self):
        for i in range(2, 8):
            n = str(i)

            # Check If Exist
            if 'T'+n in self.probe:
                if 'R' in self.probe['T'+n]:
                    if self.probe['T'+n]['R'] == 'N':
                        self.Craft_Respond['T'+n] = False
                        continue
            else:
                self.probe['T'+n] = dict()
                self.Craft_Respond['T'+n] = False
                continue

            # Update DF Value
            if 'DF' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': DF Value Not Found. Setting to 0 (N)')
                df_flag = 0
            elif self.probe['T'+n]['DF'] == 'Y':
                df_flag = 2
            else:
                df_flag = 0
            self.probe['T' + n]['DF'] = df_flag

            # Update Initial Window Size Value (W)
            if 'W' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': W Value Not Found. Setting to ECHOED (Default)')
                w_val = 'ECHOED'
            else:
                w_val = self.strhex2int(self.probe['T'+n]['W'])
            self.probe['T'+n]['W'] = w_val

            # Update O Value
            if 'O' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': O Value Not Found. Setting to Empty')
                o_val = 'EMPTY'
            else:
                o_val = self.o_parser('T'+n, 'O')
            self.probe['T'+n]['O'] = o_val

            # Update S Value
            if 'S' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': S Value Not Found. Setting to Default (A)')
                s_val = 'A'
                self.probe['T' + n]['S'] = s_val

            # Update A Value
            if 'A' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': A Value Not Found. Setting to Default (S)')
                a_val = 'S'
                self.probe['T' + n]['A'] = a_val

            # Update F Value
            if 'F' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': F Value Not Found. Setting to Default (SA)')
                f_val = 'SA'
                self.probe['T' + n]['F'] = f_val

            # Update RD Value
            if 'RD' not in self.probe['T'+n]:
                self.info('DEBUG_T' + n + ': RD Value Not Found. Setting to 0')
                self.probe['T' + n]['RD'] = '0'

            # Update TTL and Guess Value (T, TG)
            try:
                ttl_val = self.probe['T'+n]['T']
            except KeyError:
                self.info('DEBUG_T' + n + ': T Value Not Found. Setting to 0x40 (64)')
                ttl_val = '0x40'
            self.probe['T'+n]['TTL'] = ttl_val
            self.ttl = ttl_val

            try:
                ttl_val = self.probe['T'+n]['TG']
            except KeyError:
                self.info('DEBUG_T' + n + ': TG Value Not Found. Setting to 0x40 (64)')
                ttl_val = '0x40'
                pass
            self.probe['T'+n]['TTL'] = ttl_val
            self.ttl = ttl_val

    def ecn_update(self):
        if 'ECN' in self.probe:
            if 'R' in self.probe['ECN']:
                if self.probe['ECN']['R'] == 'N':
                    self.Craft_Respond['ECN'] = False
                    return
        else:
            self.probe['IE'] = dict()
            self.Craft_Respond['ECN'] = False
            return

        # Update DF Value
        if 'DF' not in self.probe['ECN']:
            self.info('DEBUG_ECN: DF Value Not Found. Setting to 0 (N)')
            df_flag = 0
        elif self.probe['ECN']['DF'] == 'Y':
            df_flag = 2
        else:
            df_flag = 0
        self.probe['ECN']['DF'] = df_flag

        # Update Initial Window Size Value (W)
        if 'W' not in self.probe['ECN']:
            self.info('DEBUG_ECN: DF Value Not Found. Setting to ECHOED (Default)')
            w_val = 'ECHOED'
        else:
            w_val = self.strhex2int(self.probe['ECN']['W'])
        self.probe['ECN']['W'] = w_val

        # Update O Value
        if 'O' not in self.probe['ECN']:
            self.info('DEBUG_ECN: O Value Not Found. Setting to Empty')
            o_val = 'EMPTY'
        else:
            o_val = self.o_parser('ECN', 'O')
        self.probe['ECN']['O'] = o_val

        # Update CC Value
        if 'CC' not in self.probe['ECN']:
            self.info('DEBUG_ECN: CC Value Not Found. Setting to ECHO (S)')
            cc_val = 'S'
            self.probe['ECN']['CC'] = cc_val

        # Update TTL and Guess Value (T, TG)
        try:
            ttl_val = self.probe['ECN']['T']
        except KeyError:
            self.info('DEBUG_ECN: T Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
        self.probe['ECN']['TTL'] = ttl_val
        self.ttl = ttl_val

        try:
            ttl_val = self.probe['ECN']['TG']
        except KeyError:
            self.info('DEBUG_ECN: TG Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
            pass
        self.probe['ECN']['TTL'] = ttl_val
        self.ttl = ttl_val

    def ie_update(self):
        # Check Responsiveness (ICMP)
        if 'IE' in self.probe:
            if 'R' in self.probe['IE']:
                if self.probe['IE']['R'] == 'N':
                    self.Craft_Respond['IE'] = False
                    return
        else:
            self.probe['IE'] = dict()
            self.Craft_Respond['IE'] = False
            return

        # Update DFI Value
        if 'DFI' not in self.probe['IE']:
            self.info('DEBUG_IE: DF Value Not Found. Setting To ECHOED (S)')
            self.probe['IE']['DFI'] = 'S'

        # Update ICMP Response Code (CD) Value
        if 'CD' not in self.probe['IE']:
            self.info('DEBUG_IE: CD Value Not Found. Setting To 0 For Both (Z)')
            self.probe['IE']['CD'] = 'Z'

        # Update TTL and Guess Value (T, TG)
        try:
            ttl_val = self.probe['IE']['T']
        except KeyError:
            self.info('DEBUG_IE: T Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
        self.probe['IE']['TTL'] = ttl_val
        self.ttl = ttl_val

        try:
            ttl_val = self.probe['IE']['TG']
        except KeyError:
            self.info('DEBUG_IE: TG Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
            pass
        self.probe['IE']['TTL'] = ttl_val
        self.ttl = ttl_val

    def u1_update(self):
        # Check Responsiveness (UDP)
        if 'U1' in self.probe:
            if 'R' in self.probe['U1']:
                if self.probe['U1']['R'] == 'N':
                    self.Craft_Respond['U1'] = False
                    return
        else:
            self.probe['U1'] = dict()
            self.Craft_Respond['U1'] = False
            return

        # Update DF Value in U1 (UDP)
        df_flag = 0
        if 'DF' in self.probe['U1']:
            if self.probe['U1']['DF'] == 'Y':
                df_flag = 2
            else:
                df_flag = 0
        else:
            self.info('DEBUG_U1: DF Value Not Found. Setting To 0')
            new_probe = 0
        self.probe['U1']['DF'] = df_flag

        # Update Returned IP Length Value RIPL (UDP)
        if 'RIPL' in self.probe['U1']:
            if self.probe['U1']['RIPL'] == 'G':
                ripl_val = 328
            else:
                ripl_val = int(self.probe['U1']['RIPL'], 16)
        else:
            self.info('DEBUG_U1: RIPL Value Not Found. Setting To 328 (G)')
            ripl_val = 328
        self.probe['U1']['RIPL'] = ripl_val

        # Update Returned ID RID (UDP)
        if 'RID' in self.probe['U1']:
            if self.probe['U1']['RID'] == 'G':
                rid_val = 4162
            else:
                rid_val = int(self.probe['U1']['RID'], 16)
        else:
            self.info('DEBUG_U1: RID Value Not Found. Setting To 4162 (G)')
            rid_val = 4162
        self.probe['U1']['RID'] = rid_val

        # Update Integrity of returned probe UDP checksum (RUCK)
        if 'RUCK' in self.probe['U1']:
            if self.probe['U1']['RUCK'] != 'G':
                ruck_val = int(self.probe['U1']['RUCK'], 16)
            else:
                ruck_val = 'G'
        else:
            self.info('DEBUG_U1: RUCK Value Not Found. Setting To Default (G)')
            ruck_val = 'G'
        self.probe['U1']['RUCK'] = ruck_val

        # Update Integrity of returned probe IP checksum value (RIPCK)
        if 'RIPCK' not in self.probe['U1']:
            self.info('DEBUG_U1: RIPCK Value Not Found. Setting to Default (G)')
            self.probe['U1']['RIPCK'] = 'G'

        # Update TTL and Guess Value (T, TG)
        try:
            ttl_val = self.probe['U1']['T']
        except KeyError:
            self.info('DEBUG_U1: T Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
        self.probe['U1']['TTL'] = ttl_val
        self.ttl = ttl_val

        try:
            ttl_val = self.probe['U1']['TG']
        except KeyError:
            self.info('DEBUG_U1: TG Value Not Found. Setting to 0x40 (64)')
            ttl_val = '0x40'
            pass
        self.probe['U1']['TTL'] = ttl_val

    def win_update(self):
        if 'WIN' in self.probe:
            if 'R' not in self.probe['WIN']:
                for key in self.probe['WIN']:
                    temp_win_value = int(self.probe['WIN'][key], 16)
                    self.probe['WIN'][key] = temp_win_value
            else:
                self.info('DEBUG_WIN: Responsiveness: NO. Setting To 0')
                self.probe['WIN'] = dict()
                for i in range(1, 7):
                    self.probe['WIN']['W' + str(i)] = 0
        else:
            self.info('DEBUG: WIN Value Not Found. Setting to 0')
            self.probe['WIN'] = dict()
            for i in range(1, 7):
                self.probe['WIN']['W' + str(i)] = None

    def ops_update(self):
        # Update OPS Value to Actual List (TCP OPTIONS)
        if 'OPS' in self.probe:
            if 'R' not in self.probe['OPS']:
                for key in self.probe['OPS']:
                    temp_o_value = self.o_parser('OPS', key)
                    self.probe['OPS'][key] = temp_o_value
            else:
                self.info('DEBUG_OPS: Responsiveness: NO. Setting To No Options')
                self.probe['OPS'] = dict()
                for i in range(1, 7):
                    self.probe['OPS']['O' + str(i)] = []
        else:
            self.info('DEBUG_OPS: OPS Value Not Found. Setting To No Options')
            self.probe['OPS'] = dict()
            for i in range(1, 7):
                self.probe['OPS']['O' + str(i)] = []

    def info(self, log):
        if self.debug:
            print(log)

    def o_parser(self, cat, key):
        temp_o_value = []
        for char in range(len(self.probe[cat][key])):

            if self.probe[cat][key][char] == 'L':
                temp_o_value.append(('EOL', None))

            if self.probe[cat][key][char] == 'N':
                temp_o_value.append(('NOP', None))

            if self.probe[cat][key][char] == 'M':
                ans = self.fwd_look(self.probe[cat][key], char + 1)
                temp_o_value.append(('MSS', ans))

            if self.probe[cat][key][char] == 'W':
                ans = self.fwd_look(self.probe[cat][key], char + 1)
                temp_o_value.append(('WScale', ans))

            if self.probe[cat][key][char] == 'T':
                TSval = (self.probe[cat][key][char + 1])
                TSecr = (self.probe[cat][key][char + 2])

                if int(TSval) == 1:
                    temp_o_value.append(('Timestamp', (4294967295, int(TSecr))))

            if self.probe[cat][key][char] == 'S':
                temp_o_value.append(('SAckOK', b''))

        return temp_o_value

    def strhex2int(self, string):
        try:
            return int(string, 16)
        except ValueError:
            return int('0x' + string, 16)

    def swapcheck(self, min_val, max_val):
        small = self.strhex2int(min_val)
        big = self.strhex2int(max_val)

        if small > big:
            small, big = big, small

        return small, big

    def fwd_look(self, string, start):
        output = []
        i = start
        while True:
            try:
                int(string[i], 16)
                output.append(string[i])
                i += 1
            except (ValueError, IndexError):
                return int('0x' + ''.join(str(e) for e in output), 16)