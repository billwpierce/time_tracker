import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import time
import datetime

project_id = 'time-tracker-27c0c'

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="time-tracker-27c0c-firebase-adminsdk-xri0q-b00058a0b6.json"

# Use the application default credentials
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': project_id,
})

db = firestore.client()
statuses = []

def add_status(status_name):
    status_doc = db.collection(u'statuses').document(status_name)
    status_doc.set({
        u'status_name': status_name,
        u'creation_time': datetime.datetime.now()
    })
    statuses.append(status_name)

def pull_statuses():
    for status in db.collection(u'statuses').get():
        stat_name = status.to_dict()["status_name"]
        if stat_name not in statuses:
            statuses.append(stat_name)

def start(status_name):
    if status_name in statuses:
        f = open("cti.txt", "r+")
        assert f.read() == "", "Currently doing another task."
        doc_name = str(datetime.datetime.now()) + status_name
        f.write(doc_name)
        time_doc = db.collection(u'time_list').document(doc_name)
        time_doc.set({ #TODO: Add try/catch for cti.txt writing
            u'status_name': status_name,
            u'start_time': datetime.datetime.now()
        })
        f.close()
    else:
        print("Status name could not be found. Closest status:", autocorrect(status_name, statuses, edit_dist, 3))

def end():
    time_doc = get_curr_task()
    doc_dict = time_doc.get().to_dict()
    start_time = doc_dict["start_time"].replace(tzinfo=None)
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print("Finished", doc_dict["status_name"] + ", Duration:", duration)
    time_doc.set({
        u'end_time': end_time,
        u'duration': duration.total_seconds()
    }, merge=True)
    f = open("cti.txt", "r+")
    f.truncate(0)
    f.close()

def get_curr_task():
    f = open("cti.txt", "r")
    task = f.read()
    assert not(task == ""), "Nothing currently happening!"
    time_doc = db.collection(u'time_list').document(task)
    f.close()
    return time_doc

def pr_status():
    ct = get_curr_task()
    print(ct.get().to_dict()["status_name"].capitalize(), "started at", ct.get().to_dict()["start_time"])

def edit_dist(start, goal, limit):
    """A diff function that computes the edit distance from START to GOAL."""
    if limit < 0:
        return 1
    if len(start) == 0:
        return len(goal)
    if len(goal) == 0:
        return len(start)
    if start[0] == goal[0]:
        return edit_dist(start[1:], goal[1:], limit)
    else:
        add_diff = edit_dist(goal[0] + start, goal, limit - 1)
        remove_diff = edit_dist(start[1:], goal, limit - 1)
        swap_diff = edit_dist(goal[0] + start[1:], goal, limit - 1)
        return 1 + min(add_diff, remove_diff, swap_diff)

def autocorrect(user_word, valid_words, diff_function, limit): # from cs61a
    """Returns the element of VALID_WORDS that has the smallest difference
    from USER_WORD. Instead returns USER_WORD if that difference is greater
    than LIMIT.
    """
    if user_word in valid_words:
        return user_word
    limit_list = [diff_function(user_word, word, limit) for word in valid_words]
    min_lim = min(limit_list)
    if min_lim <= limit:
        return valid_words[limit_list.index(min_lim)]
    else:
        return user_word

if __name__ == "__main__":
    pull_statuses()