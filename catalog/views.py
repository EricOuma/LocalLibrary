import datetime

from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from catalog.forms import RenewBookForm
from catalog.models import Book, Author, BookInstance, Genre


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    
    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    
    # The 'all()' is implied by default.    
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10
    context_object_name = 'book_list'   # your own name for the list as a template variable
    queryset = Book.objects.all()
    template_name = 'catalog/books/books_list.html'  # Specify your own template name/location


class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'catalog/books/book_detail.html'


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10
    template_name = 'catalog/authors/authors_list.html'

class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'catalog/authors/author_detail.html'


class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/books/bookinstance_list_borrowed_user.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LoanedBooksListView(LoginRequiredMixin,PermissionRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to library users."""
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    template_name ='catalog/librarian/bookinstance_list_borrowed.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')



@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('catalog') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/librarian/book_renew_librarian.html', context)


class AuthorCreate(CreateView):
    model = Author
    template_name ='catalog/authors/author_form.html'
    fields = '__all__'
    initial = {'date_of_death': '05/01/2018'}

class AuthorUpdate(UpdateView):
    model = Author
    template_name ='catalog/authors/author_form.html'
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    template_name ='catalog/authors/author_confirm_delete.html'
    success_url = reverse_lazy('authors')

class BookCreate(CreateView):
    model = Book
    template_name ='catalog/books/book_form.html'
    fields = '__all__'

class BookUpdate(UpdateView):
    model = Book
    template_name ='catalog/books/book_form.html'
    fields = '__all__'

class BookDelete(DeleteView):
    model = Book
    template_name ='catalog/books/book_confirm_delete.html'
    success_url = reverse_lazy('books')