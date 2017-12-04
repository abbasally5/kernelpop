import os
import subprocess
import platform
from pydoc import locate
from constants import LINUX_EXPLOIT_PATH, HIGH_RELIABILITY, MEDIUM_RELIABILITY, LOW_RELIABILITY, HEADER, bcolors, \
        color_print, UBUNTU_12, UBUNTU_14, UBUNTU_16, UBUNTU_GENERIC, \
        GENERIC_LINUX, CONFIRMED_VULNERABLE, POTENTIALLY_VULNERABLE, NOT_VULNERABLE, UBUNTU_7, UBUNTU_8, \
        UBUNTU_9,UBUNTU_17, DEBIAN_GENERIC, UBUNTU_15,  \
        UBUNTU_6, ARCHITECTURE_GENERIC, shell_results, MAC_EXPLOIT_PATH, GENERIC_MAC, ubuntu_distro_versions, \
        debian_distro_versions, RHEL, \
        NETBSD, OPENBSD


class Kernel:
        def __init__(self, kernel_version, uname=False):
                self.type, self.distro, self.name, self.major_version, self.minor_version, \
                self.release, self.architecture, self.uname = self.process_kernel_version(kernel_version, uname=uname)

                self.alert_kernel_discovery()

        def parse_distro(self, kernel_version):
                """
                grabs the distro name if it can from /etc/*release

                :param kernel_version: String from platform.platform()
                :return: String of distro name if it exists
                """
                if "linux" in kernel_version.lower():
                        release_command = "cat /etc/*release"
                        p = subprocess.Popen(
                                release_command,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True
                        )
                        release_result = p.communicate()[0].decode('utf-8')
                        # if there is a /etc/*release file
                        if "ubuntu" in kernel_version.lower():
                                if len(release_result) > 0:
                                        distro_id = release_result.split("\n")[0]
                                        # check if the parsed version number matches known versions
                                        for distro in ubuntu_distro_versions:
                                                distro_desc = release_result.split("\n")[3]
                                                version_num = distro_desc.split(" ")[1].split(".")[0]
                                                for v_num in distro:
                                                        if v_num[0].replace("ubuntu-","") in version_num:
                                                                return v_num[1]

                                # if there isn't a /etc/*release file, check if the known version string is in the kernel_version
                                for distro_string in ubuntu_distro_versions:
                                        if distro_string[0] in kernel_version.lower():
                                                return distro_string[1]

                                return UBUNTU_GENERIC

                        elif "debian" in kernel_version.lower():
                                return DEBIAN_GENERIC

                        elif "EL" in kernel_version:
                                return RHEL

                        # return generic
                        return GENERIC_LINUX

                elif "darwin" in kernel_version.lower():
                        return GENERIC_MAC

                elif "bsd" in kernel_version.lower():
                        bsd_type = kernel_version.split(" ")[0]
                        if "NetBSD" in bsd_type:
                                return NETBSD
                        elif "OpenBSD" in bsd_type:
                                return OPENBSD

                return "unknown"

        def process_kernel_version(self, kernel_version, uname=False):
                # running on mac
                # Darwin-16.7.0-x86_64-i686-64bit
                if "Darwin" in kernel_version:

                        if uname:
                                color_print("[+] `uname -a` os identified as a mac variant")
                                k_type = "mac"
                                k_distro = self.parse_distro(kernel_version)
                                k_name = kernel_version.split(" ")[0]
                                k_major = int(kernel_version.split(" ")[2].split(".")[0])
                                k_minor = int(kernel_version.split(" ")[2].split(".")[1])
                                k_release = int(kernel_version.split(" ")[2].split(".")[2])
                                k_architecture = kernel_version.split(" ")[-1]
                                # replace any bad architecture parses
                                for architecture in ["x86", "i686", "amd64", "x86_64"]:
                                        if architecture in kernel_version:
                                                k_architecture = architecture
                                return k_type, k_distro, k_name, k_major, k_minor, k_release, k_architecture, kernel_version
                        else:
                                color_print("[+] underlying os identified as a mac variant")
                                k_type = "mac"
                                k_distro = self.parse_distro(kernel_version)
                                k_name = kernel_version.split("-")[0]
                                k_major = int(kernel_version.split("-")[1].split(".")[0])
                                k_minor = int(kernel_version.split("-")[1].split(".")[1])
                                k_release = int(kernel_version.split("-")[1].split(".")[2])
                                k_architecture = kernel_version.split("-")[2]
                                # replace any bad architecture parses
                                for architecture in ["x86", "i686", "amd64", "x86_64"]:
                                        if architecture in kernel_version:
                                                k_architecture = architecture
                                return k_type, k_distro, k_name, k_major, k_minor, k_release, k_architecture, kernel_version

                # running on linux
                # Linux-4.10.0-37-generic-x86_64-with-Ubuntu-16.04-xenial
                elif "Linux" in kernel_version:
                        if uname:
                                color_print("[+] `uname -a` os identified as a linux variant")
                                k_type = "linux"
                                k_distro = self.parse_distro(kernel_version)
                                k_name = kernel_version.split(" ")[0]

                                k_full_version = kernel_version.split(" ")[2].split(".")
                                # the uname's first version string is in the format Major.Minor-distro-architecture instead of
                                #       the expected Major.Minor.Release-distro-architecture...try to parse from the end
                                #
                                if len(k_full_version) < 3:
                                        k_full_version = kernel_version.split(" ")[-4].split(".")
                                # if we couldn't parse out 3 again..
                                if len(k_full_version) < 3:
                                        k_full_version = kernel_version.split(" ")[-4].split(".")
                                        # minor will have garbage after a '-'
                                        k_full_version[1] = k_full_version[1].split("-")[0]
                                        k_full_version.append("0")
                                k_full_version = clean_parsed_version(k_full_version)

                                k_major = int(k_full_version[0])
                                k_minor = int(k_full_version[1])
                                k_release = int(k_full_version[2])
                                k_architecture = kernel_version.split(" ")[-2]
                                # replace any bad architecture parses
                                for architecture in ["x86", "i686", "amd64", "x86_64"]:
                                        if architecture in kernel_version:
                                                k_architecture = architecture

                                return k_type, k_distro, k_name, k_major, k_minor, k_release, k_architecture, kernel_version

                        else:
                                color_print("[+] underlying os identified as a linux variant")
                                k_type = "linux"
                                k_distro = self.parse_distro(kernel_version)
                                k_name = kernel_version.split("-")[-1]
                                k_full_version = kernel_version.split("-")[1].split(".")
                                if len(k_full_version) < 3:
                                        k_full_version.append("0")      # we just assume base kernel
                                k_full_version = clean_parsed_version(k_full_version)

                                k_major = int(k_full_version[0])
                                k_minor = int(k_full_version[1])
                                k_release = int(k_full_version[2])
                                k_architecture = kernel_version.split("-")[4]
                                # replace any bad architecture parses
                                for architecture in ["x86", "i686", "amd64", "x86_64"]:
                                        if architecture in kernel_version:
                                                k_architecture = architecture

                                return k_type, k_distro, k_name, k_major, k_minor, k_release, k_architecture, kernel_version

                # running on windows
                elif "win" in kernel_version:
                        color_print("[+] underlying os identified as a windows variant")
                        if uname:
                                color_print("[-] no uname support yet", color="red")
                                exit(0)
                        else:
                                pass
                elif "BSD" in kernel_version:
                        if uname:
                                color_print("[+] `uname -a` os identified as a BSD variant")
                                k_type = "linux"
                                k_distro = self.parse_distro(kernel_version)
                                k_name = kernel_version.split(" ")[0]

                                k_full_version = kernel_version.split(" ")[2].split(".")
                                # BSD versions only have major.minor format. Feed empty value for release
                                while len(k_full_version) < 3:
                                        k_full_version.append("0")
                                k_full_version = clean_parsed_version(k_full_version)

                                k_major = int(k_full_version[0])
                                k_minor = int(k_full_version[1])
                                k_release = int(k_full_version[2])
                                k_architecture = kernel_version.split(" ")[-1]

                                # replace any bad architecture parses
                                for architecture in ["x86", "i686", "amd64", "x86_64"]:
                                        if architecture in kernel_version:
                                                k_architecture = architecture

                                return k_type, k_distro, k_name, k_major, k_minor, k_release, k_architecture, kernel_version
                        else:
                                color_print("[+] underlying os identified as a BSD variant")
                                k_type = "linux"
                                k_distro = self.parse_distro(kernel_version)
                                k_name = kernel_version.split("-")[0]
                                k_full_version = kernel_version.split("-")[1].split(".")
                                while len(k_full_version) < 3:
                                        k_full_version.append("0") 
                                k_full_version = clean_parsed_version(k_full_version)

                                k_major = int(k_full_version[0])
                                k_minor = int(k_full_version[1])
                                k_release = int(k_full_version[2])
                                k_architecture = kernel_version.split("-")[2]
                                # replace any bad architecture parses
                                for architecture in ["x86", "i686", "amd64", "x86_64"]:
                                        if architecture in kernel_version:
                                                k_architecture = architecture

                                return k_type, k_distro, k_name, k_major, k_minor, k_release, k_architecture, kernel_version

                # don't know what we're on
                else:
                        color_print("[-] could not identify underlying os", color="red")
                        exit(1)

        def alert_kernel_discovery(self):
                if self.type == "linux":
                        color_print("[+] kernel {} identified as:\n\ttype:\t\t\t{}\n\tdistro:\t\t\t{}\n\tversion:\t\t{}-{}" \
                                                "\n\tarchitecture:\t\t{}".format(
                                self.uname, self.type, self.distro, ".".join([str(self.major_version), str(self.minor_version)]), self.release,
                                self.architecture), bold=True)
                elif self.type == "mac":
                        color_print("[+] kernel {} identified as:\n\ttype:\t\t\t{}\n\tversion:\t\t{}\n\tarchitecture:\t\t{}".format(
                                self.uname, self.type, ".".join([str(self.major_version), str(self.minor_version), str(self.release)]),
                                self.architecture), bold=True)
                elif self.type == "windows":
                        pass
                else:
                        exit(1)

def get_mac_version():
        """
        Gets the mac operating system version vs. the kernel version
        :return:
        """
        v_command = "sw_vers"
        mac_v = shell_results(v_command)[0].decode("utf-8")
        v_major = int(mac_v.split("\n")[1].split(":")[1].split(".")[0])
        v_minor = int(mac_v.split("\n")[1].split(":")[1].split(".")[1])
        try:
                v_release = int(mac_v.split("\n")[1].split(":")[1].split(".")[2])
        except:
                v_release = 0

        return v_major, v_minor, v_release


def get_kernel_version(uname=None, osx_ver=None):
        """
        get_kernel_version()

        Determines the version of the kernel running on the underlying operating system. Uses the 'platform' package to
        ensure cross-compatibility between MacOS (OS X), Windows, and Linux hosts.

        :returns: Kernel object
        """
        if not uname:
                kernel_version = {
                        "normal": platform.platform(),
                        "aliased": platform.platform(aliased=True),
                        "terse": platform.platform(terse=True)
                }
                if "darwin" in kernel_version["normal"].lower():
                        os_major, os_minor, os_release = get_mac_version()
                        version_string = "{}.{}.{}".format(os_major, os_minor, os_release)
                        template_os_version_start = kernel_version["normal"].split("-")[0]
                        template_os_version_end = "-".join(kernel_version["normal"].split("-")[2:])
                        os_version_replaced_kv = "{}-{}-{}".format(template_os_version_start, version_string, template_os_version_end)

                        return Kernel(os_version_replaced_kv)
                else:
                        return Kernel(kernel_version["normal"])
        else:
                if osx_ver:
                        uname_pre = " ".join(uname.split(" ")[:2])
                        uname_post = " ".join(uname.split(" ")[3:])
                        uname_os_version = "{} {} {}".format(uname_pre, osx_ver, uname_post)
                        return Kernel(uname_os_version, uname=True)


                else:
                        return Kernel(uname, uname=True)

def clean_parsed_version(parsed_version):
        """
        Takes in a parsed version in the form Major.Minor.Release and cleans it of any appended garbage
        Appended garbage takes the form of stuff added on that wasn't split out on the '-' character

        :param parsed_version:
        :return:
        """
        for idx, version_n in enumerate(parsed_version):
                parsed_version[idx] = version_n.split("-")[0]

        # check to make sure we got everything
        for version_n in parsed_version:
                if not version_n.isdigit():
                        Exception("DIDN'T CLEAN VERSION PROPERLY")

        return parsed_version

def potentially_vulnerable(kernel_version, exploit_module):
        """
        potentially_vulnerable(kernel_version, exploit_module)

        Identifies if a given kernel is vulnerable to a given exploit and in what capacity (i.e. Confirmed or Potential).
        Checks architecture requirements as well

        :param kernel_version: Kernel object
        :param exploit_module: Exploit object
        :return: string expressing the vulnerability state of the given Kernel object to the given Exploit object
        """
        if kernel_version.architecture == exploit_module.architecture or \
                                        exploit_module.architecture == ARCHITECTURE_GENERIC:
                vuln_results = []
                for kernel_window in exploit_module.vulnerable_kernels:
                        vuln_results.append(kernel_window.kernel_in_window(kernel_version))
                for vuln_cat in [CONFIRMED_VULNERABLE, POTENTIALLY_VULNERABLE, NOT_VULNERABLE]:
                        if vuln_cat in vuln_results:
                                return vuln_cat
        else:
                return NOT_VULNERABLE

def find_exploit_locally(kernel_version):
        """
        find_exploit_locally(Kernel kernel_version)

        Identifies potential exploits for the given kernel by dynamically loading exploit modules from the identified
        operating system's `exploit` dir and checking the kernel vs the list of vulnerable kernels in that exploit.

        :param kernel_version: Kernel() object containing kernel information
        :returns: array of arrays of exploit modules sorted in order of likelihood of success
                i.e. [ [high] [medium] [low] ]
        """
        confirmed = {
                HIGH_RELIABILITY: [],
                MEDIUM_RELIABILITY: [],
                LOW_RELIABILITY: []
        }
        potential = {
                HIGH_RELIABILITY: [],
                MEDIUM_RELIABILITY: [],
                LOW_RELIABILITY: []
        }
        found_exploits = {"confirmed": confirmed, "potential": potential}

        kernel_exploits_and_paths = [
                ["linux", LINUX_EXPLOIT_PATH],
                ["mac", MAC_EXPLOIT_PATH],
                #["bsd", LINUX_EXPLOIT_PATH] #TODO: create separate folder for BSD
        ]

        color_print("[*] matching kernel to known exploits")
        for idx,k_ex_path in enumerate(kernel_exploits_and_paths):
                if kernel_version.type == kernel_exploits_and_paths[idx][0]:
                        all_exploits = os.listdir(kernel_exploits_and_paths[idx][1])
                        for exploit_file in all_exploits:
                                if exploit_file[-3:] == ".py" and "__init__" not in exploit_file:
                                        exploit_name = exploit_file.replace(".py", "")
                                        exploit_module = locate("exploits.{}.{}.{}".format(kernel_exploits_and_paths[idx][0],exploit_name, exploit_name))
                                        exploit_instance = exploit_module()
                                        if potentially_vulnerable(kernel_version, exploit_instance) == CONFIRMED_VULNERABLE:
                                                color_print("\t[+] found `confirmed` kernel exploit: {}".format(exploit_instance.name),
                                                                        color="green")
                                                found_exploits["confirmed"][exploit_instance.reliability].append(exploit_instance)
                                        elif potentially_vulnerable(kernel_version, exploit_instance) == POTENTIALLY_VULNERABLE:
                                                color_print("\t[+] found `potential` kernel exploit: {}".format(exploit_instance.name),
                                                                        color="yellow")
                                                found_exploits["potential"][exploit_instance.reliability].append(exploit_instance)
                                        else:
                                                del exploit_module

        return found_exploits


def find_exploit_remotely(kernel_version):
        """

        :param kernel_version: dictionary of the kernel version returned from `get_kernel_version()`
        :return: array of unique exploit identifiers possible for this kernel
        """
        pass


def brute_force_enumerate(identified_exploits):
        """
        change enumeration to only cover potentials and move them to confirmed if they come back confirmed, otherwise
        drop them

        :param identified_exploits:
        :return:
        """
        # TODO: read function description
        confirmed_vulnerable = {"high":[], "medium":[], "low":[]}
        color_print("[*] attempting to confirm all discovered exploits from most to least probable")
        if len(identified_exploits[HIGH_RELIABILITY]) > 0:
                color_print("\t[[ high reliability ]]", color="green")
                for high_exploit in identified_exploits[HIGH_RELIABILITY]:
                        if high_exploit.determine_vulnerability():
                                confirmed_vulnerable["high"].append(high_exploit)
        if len(identified_exploits[MEDIUM_RELIABILITY]) > 0:
                color_print("\t[[ medium reliability ]]", color="yellow")
                for medium_exploit in identified_exploits[MEDIUM_RELIABILITY]:
                        if medium_exploit.determine_vulnerability():
                                confirmed_vulnerable["medium"].append(medium_exploit)
        if len(identified_exploits[LOW_RELIABILITY]) > 0:
                color_print("\t[[ low reliability ]]", color="red")
                for low_exploit in identified_exploits[LOW_RELIABILITY]:
                        if low_exploit.determine_vulnerability():
                                confirmed_vulnerable["low"].append(low_exploit)
        if len(identified_exploits[HIGH_RELIABILITY]) == 0 and \
                                        len(identified_exploits[MEDIUM_RELIABILITY]) == 0 and \
                                        len(identified_exploits[LOW_RELIABILITY]) == 0:
                color_print("[-] no exploits to verify for this kernel", color="red")

        return confirmed_vulnerable


def brute_force_exploit(confirmed_exploits):
        color_print("\t[*] attempting to exploit confirmed exploits", color="blue")
        if len(confirmed_exploits[HIGH_RELIABILITY]) > 0:
                color_print("\t[[ high reliability ]]", color="green")
                for high_exploit in confirmed_exploits[HIGH_RELIABILITY]:
                        high_exploit.exploit()
        if len(confirmed_exploits[MEDIUM_RELIABILITY]) > 0:
                color_print("\t[[ medium reliability ]]", color="yellow")
                for medium_exploit in confirmed_exploits[MEDIUM_RELIABILITY]:
                        medium_exploit.exploit()
        if len(confirmed_exploits[LOW_RELIABILITY]) > 0:
                color_print("\t[[ low reliability ]]", color="red")
                for low_exploit in confirmed_exploits[LOW_RELIABILITY]:
                        low_exploit.exploit()


def display_ordered_exploits(ordered_exploits, begin_message=None, fail_message=None, color=None):
        """

        :param ordered_exploits:
        :param begin_message:
        :param fail_message:
        :param color:
        :return:
        """
        if color:
                color_print(begin_message, color=color)

                # for confirmed vulnerabilities
                if len(ordered_exploits[HIGH_RELIABILITY]) > 0:
                        color_print("\t[[ high reliability ]]", color=color)
                        for high_exploit in ordered_exploits[HIGH_RELIABILITY]:
                                color_print("\t\t{}\t{}".format(high_exploit.name, high_exploit.brief_desc), color=color)
                if len(ordered_exploits[MEDIUM_RELIABILITY]) > 0:
                        color_print("\t[[ medium reliability ]]", color=color)
                        for medium_exploit in ordered_exploits[MEDIUM_RELIABILITY]:
                                color_print("\t\t{}\t{}".format(medium_exploit.name, medium_exploit.brief_desc), color=color)
                if len(ordered_exploits[LOW_RELIABILITY]) > 0:
                        color_print("\t[[ low reliability ]]", color=color)
                        for low_exploit in ordered_exploits[LOW_RELIABILITY]:
                                color_print("\t\t{}\t{}".format(low_exploit.name, low_exploit.brief_desc), color=color)
                if len(ordered_exploits[HIGH_RELIABILITY]) == 0 and \
                                                len(ordered_exploits[MEDIUM_RELIABILITY]) == 0 and \
                                                len(ordered_exploits[LOW_RELIABILITY]) == 0:
                        if fail_message:
                                color_print(fail_message, color=color)
        else:
                color_print(begin_message)

                # for confirmed vulnerabilities
                if len(ordered_exploits[HIGH_RELIABILITY]) > 0:
                        color_print("\t[[ high reliability ]]", color="green")
                        for high_exploit in ordered_exploits[HIGH_RELIABILITY]:
                                color_print("\t\t{}\t{}".format(high_exploit.name, high_exploit.brief_desc))
                if len(ordered_exploits[MEDIUM_RELIABILITY]) > 0:
                        color_print("\t[[ medium reliability ]]", color="yellow")
                        for medium_exploit in ordered_exploits[MEDIUM_RELIABILITY]:
                                color_print("\t\t{}\t{}".format(medium_exploit.name, medium_exploit.brief_desc))
                if len(ordered_exploits[LOW_RELIABILITY]) > 0:
                        color_print("\t[[ low reliability ]]", color="red")
                        for low_exploit in ordered_exploits[LOW_RELIABILITY]:
                                color_print("\t\t{}\t{}".format(low_exploit.name, low_exploit.brief_desc))
                if len(ordered_exploits[HIGH_RELIABILITY]) == 0 and \
                                                len(ordered_exploits[MEDIUM_RELIABILITY]) == 0 and \
                                                len(ordered_exploits[LOW_RELIABILITY]) == 0:
                        if fail_message:
                                color_print(fail_message, color="red")

def exploit_individually(exploit_name):
        color_print("[*] attempting to perform exploitation with exploit {}".format(exploit_name))
        exploit_os = ["linux", "windows", "mac"]
        found_exploit = False
        for os_type in exploit_os:
                exploit_path_string = "exploits.{}.{}.{}".format(os_type, exploit_name, exploit_name)
                exploit_module = locate(exploit_path_string)
                if exploit_module:
                        found_exploit = True
                        exploit_module().exploit()
        if not found_exploit:
                color_print("[-] exploit {} was not found".format(exploit_name), color="red")


def total_exploits(exploits):
        total = 0
        levels = [HIGH_RELIABILITY, MEDIUM_RELIABILITY, LOW_RELIABILITY]
        for level in levels:
                if len(exploits[level]) > 0:
                        total += len(exploits[level])

        return total

def kernelpop(mode="enumerate", uname=None, exploit=None, osx_ver=None):
        """
        kernelpop()

        Runs the show
        :return:
        """

        color_print(HEADER, color="blue", bold=True)
        if exploit:
                exploit_individually(str(exploit))
        else:
                if uname:
                        if osx_ver:
                                kernel_v = get_kernel_version(uname=uname, osx_ver=osx_ver)
                        else:
                                kernel_v = get_kernel_version(uname=uname)
                else:
                        kernel_v = get_kernel_version()

                identified_exploits = find_exploit_locally(kernel_v)
                display_ordered_exploits(identified_exploits["confirmed"],
                        begin_message="[*] matched kernel to the following confirmed exploits",
                        fail_message="[-] no confirmed exploits were discovered for this kernel")
                display_ordered_exploits(identified_exploits["potential"],
                        begin_message="[*] matched kernel to the following potential exploits:",
                        fail_message="[-] no potential exploits were discovered for this kernel", color="yellow")

                merged_exploits = {}
                for key_val in identified_exploits["confirmed"]:
                        merged_exploits[key_val] = identified_exploits["confirmed"][key_val] + identified_exploits["potential"][key_val]

                if total_exploits(merged_exploits) > 0:
                        if "brute" in mode:
                                confirmed_vulnerable = brute_force_enumerate(merged_exploits)
                                display_ordered_exploits(confirmed_vulnerable, begin_message="[+] confirmed exploits",
                                                                                 fail_message="[-] no exploits were confirmed for this kernel")
                                if "exploit" in mode:
                                        brute_force_exploit(confirmed_vulnerable)


if __name__ == "__main__":
        kernelpop()
