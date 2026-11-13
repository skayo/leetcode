# Definition for singly-linked list.
# class ListNode(object):
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution(object):
    def mergeTwoLists(self, list1, list2):
        """
        :type list1: Optional[ListNode]
        :type list2: Optional[ListNode]
        :rtype: Optional[ListNode]
        """

        # create a starting node
        # compare the vals at both list pointers 
        # append the smaller value to the new list 
        # advance that pointers list
        # advance the new lists pointer 
        # repeat until one of the lists is empty
        # attach the remaining values to the new list
