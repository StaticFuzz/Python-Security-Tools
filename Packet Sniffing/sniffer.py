import socket
import struct


def main():
    # needs network interface set to Promiscuous mode(ifconfig "interface" promisc
    sniffer = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))  # only IP packets

    while True:
        try:
            packet = sniffer.recvfrom(65565)
            deconstruct_packet(packet[0])
        except KeyboardInterrupt:
            break

    sniffer.close()


def deconstruct_packet(pkt):
    # deconstruct ethernet frame
    ethernet_header = struct.unpack("!6s6sH", pkt[0:14])
    destination_mac = ethernet_header[0]  # the mac addresses need to be deconstructed
    source_mac = ethernet_header[1]

    ip_header = struct.unpack("!BBHHHBBH4s4s", pkt[14:34])
    version_length = ip_header[0]
    ip_version = version_length >> 4
    ip_header_length = version_length & 0xF
    ip_payload = pkt[ip_header_length:]
    ip_protocol = ip_header[6]
    source_address = socket.inet_ntoa(ip_header[8])
    destination_address = socket.inet_ntoa(ip_header[9])

    if ip_protocol == 1:
        protocol_name = "ICMP"
        protocol_header = struct.unpack("!BBH", ip_payload[0:4])
        source_port = 0
        destination_port = 0
        protocol_payload = ip_payload[4:]
    elif ip_protocol == 6:
        protocol_name = "TCP"
        protocol_header = struct.unpack("!HHLLBBHHH", ip_payload[0:20])
        protocol_header_length = protocol_header[4] >> 4
        source_port = protocol_header[0]
        destination_port = protocol_header[1]
        protocol_payload = ip_payload[protocol_header_length:]
    elif ip_protocol == 17:
        protocol_name = "UDP"
        protocol_header = struct.unpack("!HHHH", ip_payload[0:8])
        source_port = protocol_header[0]
        destination_port = protocol_header[1]
        protocol_header_length = protocol_header[2]
        protocol_payload = ip_payload[protocol_header_length:]
    else:
        return

    source = (source_address, source_port)
    destination = (destination_address, destination_port)

    print("protocol: {}\t{}\t->\t{}".format(protocol_name, source, destination))


if __name__ == "__main__":
    main()

