"""
Module containing a GUID_MAP, mapping GPT UUID to a hexcode (inspired in gdisk)
"""

# Maps GUID to hex code.
# See https://sourceforge.net/p/gptfdisk/code/ci/master/tree/parttypes.cc#l75
GUID_MAP = {
    # Windows
    'EBD0A0A2-B9E5-4433-87C0-68B6B72699C7': 0x0700,  # Microsoft basic data (NTFS)
    'E3C9E316-0B5C-4DB8-817D-F92DF00215AE': 0x0C01,  # Microsoft reserved
    'DE94BBA4-06D1-4D40-A16A-BFD50179D6AC': 0x2700,  # Windows recovery

    # EFI and boot related
    'C12A7328-F81F-11D2-BA4B-00A0C93EC93B': 0xEF00,  # EFI System Partition
    '21686148-6449-6E6F-744E-656564454649': 0xEF02,  # BIOS boot partition (grub)

    # Linux
    '0657FD6D-A4AB-43C4-84E5-0933C84B4F4F': 0x8200,  # Linux swap
    '0FC63DAF-8483-4772-8E79-3D69D8477DE4': 0x8300,  # Linux filesystem
    'E6D6D379-F507-44C2-A23C-238F2A3DF928': 0x8E00,  # Linux LVM

    # Apple
    '426F6F74-0000-11AA-AA11-00306543ECAC': 0xAB00,  # Recovery HD
    '48465300-0000-11AA-AA11-00306543ECAC': 0xAF00,  # HFS/HFS+
}
