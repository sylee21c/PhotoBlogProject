from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .forms import PostForm
from .models import Post
from .permissions import IsOwnerOrReadOnly
from .serializers import PostSerializer
from .pagination import OptionalPostPagination

def visible_posts():
    return Post.objects.select_related('author').filter(published_date__lte=timezone.now())

def filter_posts(queryset, query, ordering):
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(text__icontains=query))
    choices = {'newest': ('-published_date', '-pk'), 'oldest': ('published_date', 'pk'), 'title': ('title', 'pk')}
    return queryset.order_by(*choices.get(ordering, choices['newest']))

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    pagination_class = OptionalPostPagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    def get_queryset(self):
        return filter_posts(visible_posts(), self.request.query_params.get('q', '').strip(),
                            self.request.query_params.get('ordering', 'newest'))
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class LoginThrottle(AnonRateThrottle):
    scope = 'login'

class LoginTokenView(ObtainAuthToken):
    throttle_classes = [LoginThrottle]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_profile(request):
    return Response({'id': request.user.pk, 'username': request.user.username})

def health(request):
    # A database query distinguishes an alive web process from a functioning service.
    return JsonResponse({'status': 'ok', 'service': 'PhotoBlog', 'posts': visible_posts().count()})

def post_list(request):
    query = request.GET.get('q', '').strip()
    ordering = request.GET.get('ordering', 'newest')
    return render(request, 'blog/list.html', {'posts': filter_posts(visible_posts(), query, ordering),
                                             'query': query, 'ordering': ordering})

def post_detail(request, pk):
    return render(request, 'blog/detail.html', {'post': get_object_or_404(visible_posts(), pk=pk)})

@login_required
def post_new(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('post-detail', pk=post.pk)
    return render(request, 'blog/edit.html', {'form': form, 'editing': False})

@login_required
@require_http_methods(['GET', 'POST'])
def post_edit(request, pk):
    post = get_object_or_404(visible_posts(), pk=pk)
    if post.author_id != request.user.pk:
        raise PermissionDenied
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('post-detail', pk=post.pk)
    return render(request, 'blog/edit.html', {'form': form, 'post': post, 'editing': True})

@login_required
@require_http_methods(['GET', 'POST'])
def post_delete(request, pk):
    post = get_object_or_404(visible_posts(), pk=pk)
    if post.author_id != request.user.pk:
        raise PermissionDenied
    if request.method == 'POST':
        post.delete()
        return redirect('post-list')
    return render(request, 'blog/delete.html', {'post': post})
