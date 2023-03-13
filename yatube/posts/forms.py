from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        text = forms.CharField(
            required=True,
            widget=forms.Textarea,
        )
        group = forms.ChoiceField(required=False)
        image = forms.ImageField()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        text = forms.CharField(
            required=True,
            widget=forms.Textarea,
        )
