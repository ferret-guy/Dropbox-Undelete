from datetime import datetime, timedelta
import dropbox
import sys
import os


# from this stackoverflow anwser http://stackoverflow.com/a/38322062/4492611
class Stack:
	def __init__(self):
		self.items = []

	def push(self, item):
		self.items.append(item)

	def pop(self):
		return self.items.pop()

	def peek(self):
		return self.items[0]

	def isEmpty(self):
		return len(self.items) == 0

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print "Usage:\n\tdropbox_restore <app_key> <app_secret> <days_to_subtract>"
		print "\tWhere days_to_subtract is the number of days to restore files"
		sys.exit(0)
	# Dropbox code taken from their excellent example
	# https://www.dropbox.com/developers-v1/core/start/python
	days_to_subtract = sys.argv[3]
	app_key = sys.argv[1]
	app_secret = sys.argv[2]
	flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
	authorize_url = flow.start()
	print '1. Go to: ' + authorize_url
	print '2. Click "Allow" (you might have to log in first)'
	print '3. Copy the authorization code.'
	code = raw_input("Enter the authorization code here: ").strip()
	access_token, user_id = flow.finish(code)
	client = dropbox.client.DropboxClient(access_token)

	# Recursivly get all deleted files and folders
	deleted_paths = []
	dirs = Stack()
	dirs.push('/')
	while not dirs.isEmpty():
		os.system('cls' if os.name == 'nt' else 'clear')
		print "["
		for item in dirs.items:
			try:
				# sometimes file paths or names can contain non ASCII chars
				# just don't display those file names
				print item
			except UnicodeEncodeError:
				pass
		print "] Stack Depth:{} deleted paths:{}".format(len(dirs.items),
											len(deleted_paths))
		files = client.metadata(dirs.pop(), include_deleted=True)
		for item in files['contents']:
			if item["is_dir"]:
				dirs.push(item["path"].encode("utf-8"))
			try:
				# Items without is_deleted feild are not deleted
				if item['is_deleted']:
					deleted_paths.append(item["path"])
			except KeyError:
				pass

	# Parse through the files and restore all the ones that were deleted less than
	# days_to_subtract ago
	d = datetime.today() - timedelta(days=int(days_to_subtract))
	for n, i in enumerate(deleted_paths):
		print "({}/{}): {}".format(n+1, len(deleted_paths), i.strip())
		try:
			out = client.revisions(i.strip())
			date_object = datetime.strptime(out[0]['modified'][:-6],
									"%a, %d %b %Y %H:%M:%S")
			if d < date_object:
				client.restore(i.strip(), out[0]['rev'])
			else:
				print "File too old!"
		except dropbox.rest.ErrorResponse, e:
			# Dropbox does not keep revisions of folders so we ignore them
			print "folder! not file"
			if str(e) != "[400] u'Revisions are not available for folders'":
				raise e
