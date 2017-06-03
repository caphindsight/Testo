import pymongo

from manager import *


class AuthorizationException(Exception):
  def __init__(self, msg):
    super(AuthorizationException, self).__init__(msg)

class AccessDeniedException(Exception):
  def __init__(self, msg):
    super(AccessDeniedException, self).__init__(msg)


class UsersManager(Manager):
  def __init__(self, col_users):
    super(UsersManager, self).__init__(col_users, 'user')

  def authorize(self, user, user_token):
    try:
      user_obj = self.lookup(user)
      if user_obj['token'] != user_token:
        raise AuthorizationException('Invalid security token for user %s' % user)
      if user_obj['blocked'] is True:
        raise AuthorizationException('User %s was blocked' % user)
      return user_obj
    except RecordNotFoundException:
      raise AuthorizationException('User not found: %s' % user)

  def authorize_admin(self, user, user_token):
    user_obj = self.authorize(user, user_token)
    if user_obj['admin'] is not True:
      raise AccessDeniedException('Access denied for user \'%s\'' % user)
    return user_obj

  def is_admin(self, user):
    user_obj = self.lookup(user)
    if user_obj is not None:
      return user_obj.get('admin') == True
    else:
      return False
