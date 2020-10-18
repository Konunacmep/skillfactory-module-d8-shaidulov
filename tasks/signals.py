from django.db.models.signals import m2m_changed, post_delete, post_save
from django.db.models import F
from django.dispatch import receiver
from tasks.models import TodoItem, Category
from collections import Counter
from django.core.cache import cache

# почему-то нет никакого сигнала от through при удалении задачи а не связи, поэтому будем смотреть еще сигнал
@receiver(post_delete, sender=TodoItem)
def task_counter(**kwargs):
    cat_counter = Counter()
    for cat in Category.objects.all():
        cat_counter[cat.pk] = 0
        for task in cat.todoitem_set.all():
            cat_counter[cat.pk] += 1
    for pk, new_count in cat_counter.items():
        Category.objects.filter(pk=pk).update(todos_count=new_count)
    return

@receiver(m2m_changed, sender=TodoItem.category.through)
def task_cats_add_remove(sender, instance, action, model, **kwargs):
    if action == "post_add":
        Category.objects.filter(pk__in=kwargs.get('pk_set')).update(todos_count=F('todos_count') + 1)
    if action == "post_remove":
        Category.objects.filter(pk__in=kwargs.get('pk_set')).update(todos_count=F('todos_count') - 1)  
    return

def priority_counter():
    prio_count = Counter()
    for task in TodoItem.objects.all():
        prio_count[task.get_priority_display()] += 1
    prio_count = dict(prio_count)      
    cache.set('prio_count', prio_count)
    return prio_count

@receiver(post_save, sender=TodoItem)
def priority_counters(**kwargs):
    priority_counter()
    return