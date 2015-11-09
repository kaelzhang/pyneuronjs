# We need an ordered unique list
# which should be able to swap items,
# so we have to implement by ourself
class uniqueOrderedList(list):
  def __iadd__(self, other):
    if type(other) is not list and type(other) is not self.__class__:
      # Actually, it will fail
      return super(self.__class__, self).__add__(other)

    for item in other:
      # In python, `+=` will change the referenced list object,
      # even if passed as a parameter to a function, 
      # unlike javascript and many other languages.
      # So, we need to change the original list
      self.push(item)
    return self

  def __add__(self, other):
    new = uniqueList()
    new += self
    new += other
    return new

  # push unique
  def push(self, item):
    if item not in self:
      self.append(item)

  def swap(self, index_a, index_b):
    self[index_a], self[index_b] = self[index_b], self[index_a]
