# -*- coding: utf-8 -*-
# pylint: disable-msg=W0232, R0903, W0131

"""
feedjack
Gustavo Picón
models.py
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _ 
from django.utils.encoding import smart_unicode

#from feedjack import fjcache
from feedjack_update import Dispatcher
import optparse

SITE_ORDERBY_CHOICES = (
    (1, _('Date published.')),
    (2, _('Date the post was first obtained.'))
)

#VERSION = '0.9.16'
#URL = 'http://www.feedjack.org/'
#USER_AGENT = 'Feedjack %s - %s' % (VERSION, URL)
#SLOWFEED_WARNING = 10
#ENTRY_NEW, ENTRY_UPDATED, ENTRY_SAME, ENTRY_ERR = range(4)
#FEED_OK, FEED_SAME, FEED_ERRPARSE, FEED_ERRHTTP, FEED_ERREXC = range(5)

#class Link(models.Model):
    #name = models.CharField(_('name'), max_length=100, unique=True)
    #link = models.URLField(_('link'), verify_exists=True)
        
    #class Meta:
        #verbose_name = _('link')
        #verbose_name_plural = _('links')

    #class Admin:
        #pass

    #def __unicode__(self):
        #return u'%s (%s)' % (self.name, self.link)



class Site(models.Model):
    name = models.CharField(_('name'), max_length=100)
    url = models.CharField(_('url'),
      max_length=100,
      unique=True,
      help_text=u'%s: %s, %s' % (smart_unicode(_('Example')),
        u'http://www.planetexample.com',
        u'http://www.planetexample.com:8000/foo'))
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    welcome = models.TextField(_('welcome'), null=True, blank=True)
    greets = models.TextField(_('greets'), null=True, blank=True)

    default_site = models.BooleanField(_('default site'), default=False)
    posts_per_page = models.IntegerField(_('posts per page'), default=20)
    order_posts_by = models.IntegerField(_('order posts by'), default=1,
        choices=SITE_ORDERBY_CHOICES)
    tagcloud_levels = models.IntegerField(_('tagcloud level'), default=5)
    show_tagcloud = models.BooleanField(_('show tagcloud'), default=True)
    
    use_internal_cache = models.BooleanField(_('use internal cache'), default=True)
    cache_duration = models.IntegerField(_('cache duration'), default=60*60*24,
        help_text=_('Duration in seconds of the cached pages and data.') )

    links = models.ManyToManyField(Link, verbose_name=_('links'),
      null=True, blank=True)
    template = models.CharField(_('template'), max_length=100, null=True,
      blank=True, 
      help_text=_('This template must be a directory in your feedjack '
        'templates directory. Leave blank to use the default template.') )

    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self):
        if not self.template:
            self.template = 'default'
        # there must be only ONE default site
        defs = Site.objects.filter(default_site=True)
        if not defs:
            self.default_site = True
        elif self.default_site:
            for tdef in defs:
                if tdef.id != self.id:
                    tdef.default_site = False
                    tdef.save()
        self.url = self.url.rstrip('/')
        fjcache.hostcache_set({})
        super(Site, self).save()




class Feed(models.Model):
    feed_url = models.URLField(_('feed url'), unique=True)

    is_ics = models.BooleanField(_('is_ics'), default=False)

    name = models.CharField(_('name'), max_length=100)
    shortname = models.CharField(_('shortname'), max_length=255)
    is_active = models.BooleanField(_('is active'), default=True,
        help_text=_('If disabled, this feed will not be further updated.') )

    title = models.CharField(_('title'), max_length=200, blank=True)
    tagline = models.TextField(_('tagline'), blank=True)
    link = models.URLField(_('link'), blank=True)

    # http://feedparser.org/docs/http-etag.html
    etag = models.CharField(_('etag'), max_length=255, blank=True)
    last_modified = models.DateTimeField(_('last modified'), null=True, blank=True)
    last_checked = models.DateTimeField(_('last checked'), null=True, blank=True)

    class Meta:
        verbose_name = _('feed')
        verbose_name_plural = _('feeds')
        ordering = ('name', 'feed_url',)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.feed_url)

    def save(self):
        super(Feed, self).save()
        if self.last_checked == None and self.is_ics == 'False':
          parser = optparse.OptionParser(usage='%prog [options]')
          #parser.add_option('--settings',
      #help='Python path to settings module. If this isn\'t provided, ' \
           #'the DJANGO_SETTINGS_MODULE enviroment variable will be used.')
          parser.add_option('-f', '--feed', action='append',
      help='A feed url to be updated. This option can be given multiple ' \
           'times to update several feeds at the same time ')
          #parser.add_option('-s', '--site', type='int',
      #help='A site id to update.')
          #parser.add_option('-v', '--verbose', action='store_true',
      #dest='verbose', default=False, help='Verbose output.')
          #parser.add_option('-t', '--timeout', type='int', default=10,
      #help='Wait timeout in seconds when connecting to feeds.')
          #parser.add_option('-w', '--workerthreads', type='int', default=10,
      #help='Worker threads that will fetch feeds in parallel.')
          options = parser.parse_args()[0]
          options.feed = self.feed_url              
          disp = Dispatcher(options, 10, None)
          disp.add_job(self)
          super(Feed, self).save()


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=255, unique=True)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name

    def save(self):
        super(Tag, self).save()

class Post(models.Model):
    feed = models.ForeignKey(Feed, verbose_name=_('feed'), null=False, blank=False)
    title = models.CharField(_('title'), max_length=255)
    link = models.URLField(_('link'), )
    content = models.TextField(_('content'), blank=True)
    date_modified = models.DateTimeField(_('date modified'), null=True, blank=True)
    guid = models.CharField(_('guid'), max_length=200, db_index=True)
    author = models.CharField(_('author'), max_length=255, blank=True)
    author_email = models.EmailField(_('author email'), blank=True)
    comments = models.URLField(_('comments'), blank=True)
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'))
    date_created = models.DateField(_('date created'), auto_now_add=True)

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ('-date_modified',)
        unique_together = (('feed', 'guid'),)

    def __unicode__(self):
        return self.title

    def save(self):
        super(Post, self).save()

    def get_absolute_url(self):
        return self.link



#class Subscriber(models.Model):
    #site = models.ForeignKey(Site, verbose_name=_('site') )
    #feed = models.ForeignKey(Feed, verbose_name=_('feed') )

    #name = models.CharField(_('name'), max_length=100, null=True, blank=True,
        #help_text=_('Keep blank to use the Feed\'s original name.') )
    #shortname = models.CharField(_('shortname'), max_length=50, null=True,
      #blank=True,
      #help_text=_('Keep blank to use the Feed\'s original shortname.') )
    #is_active = models.BooleanField(_('is active'), default=True,
        #help_text=_('If disabled, this subscriber will not appear in the site or '
        #'in the site\'s feed.') )

    #class Meta:
        #verbose_name = _('subscriber')
        #verbose_name_plural = _('subscribers')
        #ordering = ('site', 'name', 'feed')
        #unique_together = (('site', 'feed'),)

    #def __unicode__(self):
        #return u'%s in %s' % (self.feed, self.site)

    #def get_cloud(self):
        #from feedjack import fjcloud
        #return fjcloud.getcloud(self.site, self.feed.id)

    #def save(self):
        #if not self.name:
            #self.name = self.feed.name
        #if not self.shortname:
            #self.shortname = self.feed.shortname
        #super(Subscriber, self).save()


#~
