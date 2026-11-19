class Solution(object):
    def countBits(self, n):
        """
        :type n: int
        :rtype: List[int]
        """
        # for every number up until n starting at 0
            # at that index, count the number of on bits
            # update the value at that index to the number of count bits
        # return the array
