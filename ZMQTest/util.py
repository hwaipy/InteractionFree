__license__ = "GNU General Public License v3"
__author__ = 'Hwaipy'
__email__ = 'hwaipy@gmail.com'


# def split_address(msg):
#     """Function to split return Id and message received by ROUTER socket.
#
#     Returns 2-tuple with return Id and remaining message parts.
#     Empty frames after the Id are stripped.
#     """
#     ret_ids = []
#     for i, p in enumerate(msg):
#         if p:
#             ret_ids.append(p)
#         else:
#             break
#     return (ret_ids, msg[i + 1:])
#

class IFDefinition:
    PROTOCOL = 'IF1'
    DISTRIBUTING_MODE_BROKER = b'0x00'
    DISTRIBUTING_MODE_DIRECT = b'0x01'
    DISTRIBUTING_MODE_SERVICE = b'0x02'
