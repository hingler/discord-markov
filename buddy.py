import discord
import re
import random
import sys


class ChainEntry:
  def __init__(self):
    # set of strs representing children
    self.children = {}


class DubsClient(discord.Client):
  def __init__(self, my_id, my_command):
    super().__init__()
    # initialize with empty string
    self.seq_tree = {"": ChainEntry()}
    self.max_chain_size = 3
    self.id = my_id
    self.command = my_command
    self.save_every = 10
    self.ctr = 0
    self.read_from_file()
    self.msg_cache = open(f"msg_cache_{self.id}.txt", "a")



  def save_to_file(self):
    filename = f"markov_cache_{self.id}.txt"
    strs = {}
    i = 0
    file_dst = open(filename, "w")
    for markov_key in self.seq_tree.keys():
      strs[markov_key] = i;
      file_dst.write(markov_key + "\n")
      i = i + 1;

    file_dst.write("\n")
    # use strs for line lookup
    for markov_key in self.seq_tree.keys():
      src = strs[markov_key]
      for child in self.seq_tree[markov_key].children.keys():
        bucket = markov_key.split()
        bucket.append(child)
        if len(bucket) > self.max_chain_size:
          bucket.pop(0)
        
        child_key = " ".join(bucket)
        print("child: " + child_key)
        print("parent: " + markov_key)
        dst = strs[child_key]
        occs = self.seq_tree[markov_key].children[child]
        file_dst.write(f"{src} {dst} {occs}\n")
        # write line corresponding
    file_dst.close()

  def read_from_file(self):
    filename = f"markov_cache_{self.id}.txt"
    try:
      with open(filename, "r") as file_src:
        strs = [""]
        # skip first line
        file_src.readline()
        line = file_src.readline()
        line = line.rstrip('\n')
        while line != "":
          strs.append(line)
          self.seq_tree[line] = ChainEntry()
          print(f"entry {len(strs) - 1}: '{line}'")
          line = file_src.readline()
          line = line.rstrip('\n')
        # next line is cache entry
        line = file_src.readline().rstrip("\n")
        while line != "":
          data = [int(i) for i in line.split()]
          src = strs[data[0]]
          dst_arr = strs[data[1]].split()
          # get last word of dst
          dst = dst_arr[len(dst_arr) - 1]
          self.seq_tree[src].children[dst] = data[2]
          print(f"{src} -> {' '.join(dst_arr)} : {data[2]}")
          line = file_src.readline().rstrip("\n")
    except IOError:
      print("no cache found -- creating a fresh instance")



  async def on_message(self, message):
    if message.clean_content == "+stop":
      await self.close()
    elif message.clean_content == f"+{self.command}":
      start = self.seq_tree[""]
      msg = []
      bucket = []
      last = ""
      MAX_MSG_SIZE = 32
      while last != "END" and len(msg) < MAX_MSG_SIZE:
        occs = 0
        for child in start.children.keys():
          print("child: " + child)
          occs = occs + start.children[child]
        sel = random.randrange(0, occs + 1)
        print(f"randnum: {sel}")
        occs_pick = 0
        for child in start.children.keys():
          occs_pick = occs_pick + start.children[child]
          print(f"calculating: {child}")
          print(f"occs: {start.children[child]}")
          if occs_pick >= sel:
            # got our mark
            print(f"grabbing: {child}")
            last = child
            print(f"new end: {last}")
            if last == "END":
              break
            msg.append(last)
            bucket.append(last)
            if len(bucket) > self.max_chain_size:
              bucket.pop(0)
            # bucket
            start = self.seq_tree[" ".join(bucket)]
            break
      
      # send
      await message.channel.send(" ".join(msg))

    elif (message.author.id == self.id):
      # my id
      # read the message and add it to the tree
      c = message.clean_content
      self.msg_cache.write(c + "\n")
      if len(c) <= 0:
        # do not read empty messages
        return

      if "https://" in c or "http://" in c:
        # ignore links generally
        return

      if c.startswith("+"):
        # ignore bot syntax
        return

      # shit workaround for capitalization on mobile
      c.replace("I'", "i'")
      c.replace(" I ", " i ")

      if c[0] == "I" and c[1] == " ":
        c[0] = "i"


      strs = c.split()
      # use this to represent the end of a message
      strs.append("END")
      bucket = []
      parent = self.seq_tree[""]
      for i in strs:
        print(i)
        # add to bucket
        bucket.append(i)
        # keep below some length
        if len(bucket) > self.max_chain_size:
          bucket.pop(0)
        
        combine = " ".join(bucket)
        # merge string on spaces
        if combine not in self.seq_tree.keys():
          print(f"new bucket: {' '.join(bucket)}")
          self.seq_tree[combine] = ChainEntry()
        

        if i not in parent.children:
          parent.children[i] = 1
        else:
          parent.children[i] = parent.children[i] + 1

        parent = self.seq_tree[combine]
      self.ctr = self.ctr + 1
      if self.ctr == self.save_every:
        self.ctr = self.ctr - self.save_every
        print("saving markov data to file...")
        self.save_to_file()

  def __del__(self):
    self.save_to_file()
    self.msg_cache.close()

def main():
  argc = len(sys.argv)
  argv = sys.argv

  if (argc < 4):
    print("USAGE: py buddy.py <id> <command> <token>")
    return

  my_id = int(sys.argv[1])
  my_command = sys.argv[2]
  client = DubsClient(my_id, my_command)
  client.run(sys.argv[3])

if __name__ == "__main__":
  main()
