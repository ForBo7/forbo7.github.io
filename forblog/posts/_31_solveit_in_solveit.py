from fasthtml.common import *
bsc_hdrs = (
    Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),  # Need to download first.
    Link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.6/dist/basecoat.cdn.min.css'),
    Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.6/dist/js/all.min.js', defer=True),
)
app = FastHTML(hdrs=(bsc_hdrs, MarkdownJS(), HighlightJS(langs=['python'])), session_cookie='mysessioncookie', debug=True)
rt = app.route
from fastlite import *
db = database('solvish.db')
class User: id:int; restore_code:str
class Dialog: id:int; uid:int; dialog_num:int; name:str; messages:str; server_session:str
users = db.create(User, transform=True)
dialogs = db.create(Dialog, pk=('uid', 'dialog_num'), transform=True)
from lisette.core import *
from toolslm.shell import get_shell

sp = 'Respond in the language the user uses; The user has access to a Python interpreter that you can view; NEVER copy the format of the code interpreter messsages in your response.'
def make_chat(hist=[]): return Chat('moonshot/kimi-k2-0711-preview', hist=hist, sp=sp), get_shell()
os.environ['MOONSHOT_API_BASE'] = 'https://api.moonshot.cn/v1'
from coolname import generate_slug

@rt
def create_dialog(session):
    uid = session.get('userid')
    existing = dialogs(where=f'uid={uid}')
    dnum = max((d.dialog_num for d in existing), default=0) + 1
    session['current_dialog'] = dnum
    dialogs.insert(uid=uid, dialog_num=dnum, name=generate_slug(2), messages='[]')
    user_chats[(uid,dnum)] = make_chat()
    return Div(hx_get=f'/dialog?dnum={dnum}', hx_trigger='load', hx_target='#content', hx_swap='innerHTML')
user_chats = {}

def ensure_user(session):
    uid = session.get('userid')
    if not uid or uid not in users:
        u = users.insert(restore_code=generate_slug(3))
        session['userid'] = u.id
    return session['userid']
from fastcore.all import *
import json

def ensure_dialog(session):
    uid, dnum = map(session.get, ('userid', 'current_dialog'))
    if (uid, dnum) in user_chats: return
    elif dnum and (uid, dnum) in dialogs: 
        d = dialogs[(uid, dnum)]
        user_chats[(uid, dnum)] = make_chat(json.loads(d.messages))
    else: create_dialog(session)

from contextvars import ContextVar
current_lang = ContextVar('lang', default='en'); current_lang
@rt
def setsession(session):
    current_lang.set(session.setdefault('lang', 'en'))
    uid = ensure_user(session)
    ensure_dialog(session)
T = {
    'zh': {
        'input_placeholder': '输入内容···',
        'submit': '提交',
        'ask_model': '问问模型···',
        'your_code': '你的代码···',
        'any_thoughts': '有啥想法···',
        'enter_code': '输入代码···',
        'code': '代码',
        'prompt': '题词',
        'note': '笔记',
        'tab': '标签',
        'all_dialogs': '所有对话',
        'new_dialog': '新对话',
        'delete': '删除',
        'save': '保存',
        'solveit_lite': 'solveit-轻量版',
        'footer': '由 FastHTML 匠心打造',
        'restore_code': '恢复码',
        'restore_failed': '‼ 恢复失败',
        'restore_error': '找不到与此恢复码关联的账户，请检查后重试。',
        'enter_restore_code': '输入恢复码···',
    },
    'en': {
        'input_placeholder': 'Enter content...',
        'submit': 'Submit',
        'ask_model': 'Ask the model...',
        'your_code': 'Your code...',
        'any_thoughts': 'Any thoughts...',
        'enter_code': 'Enter code...',
        'code': 'Code',
        'prompt': 'Prompt',
        'note': 'Note',
        'tab': 'Tab',
        'all_dialogs': 'All Dialogs',
        'new_dialog': 'New Dialog',
        'delete': 'Delete',
        'save': 'Save',
        'solveit_lite': 'solveit-lite',
        'footer': 'Crafted with FastHTML',
        'restore_code': 'Restore Code',
        'restore_failed': '‼ Restore Failed',
        'restore_error': 'No account found with this restore code. Please check and try again.',
        'enter_restore_code': 'Enter restore code...',
    }
}
def t(key, session=None): 
    lang = session.get('lang', 'zh') if session else current_lang.get()
    return T[lang].get(key, key)
def Bubble(text, color, type='q', marked=True):
    colors = {
        'code': 'border-blue-500 bg-blue-50',
        'note': 'border-green-500 bg-green-50',
        'prompt': 'border-red-500 bg-red-50'
    }
    cls = f"{'marked' if marked else ''} {'ml-6' if type=='r' else ''} flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-3 py-2 text-sm border-2 {colors[color]}"
    return Div(text, cls=cls)
import fasthtml.components as fc
def mk_comp(name, def_cls):
    comp = getattr(fc, name)
    globals()[name] = lambda *args, var='', cls='', **kwargs: comp(*args, cls=f'{def_cls}{"-"+var if var else ""} {cls}', **kwargs)
mk_comp('Button', 'btn')
mk_comp('Input', 'input')
mk_comp('Textarea', 'textarea')
mk_comp('Label', 'label')
def Inp(type='text', placeholder='输入内容···', id='inp', oob=False, **kwargs): 
    return Textarea(type='text', rows=1, placeholder=placeholder, id=id, cls='font-mono', **(dict(hx_swap_oob='true') if oob else {}), **kwargs)
def get_chat(session): return user_chats[(session['userid'], session['current_dialog'])]
def sync_hist(session, hist): dialogs.update(uid=session['userid'], dialog_num=session['current_dialog'], messages=json.dumps([h.model_dump() if hasattr(h, 'model_dump') else h for h in hist]))
def mk_reply(inp, out, color, name='inp', placeholder='输入内容···'): return Inp(oob=True, name=name, placeholder=placeholder, onkeydown="if(event.shiftKey && event.key==='Enter') { event.preventDefault(); this.form.requestSubmit(); }"), Div(cls='space-y-0.5')(
    Bubble(inp, color), 
    Bubble(out, color, 'r') if out else None)
def add_hist(hist, type, content='', role='user'):
    hist.append(dict(role=role, content=content, type=type))
import json
@rt
def ask_llm(qry:str, session):
    c,sh = get_chat(session)
    res = c(qry)
    content = res.choices[0].message.content
    c.hist[-2]['type'] = 'prompt'
    c.hist[-1]['type'] = 'prompt'
    sync_hist(session, c.hist)
    return mk_reply(qry, content, 'prompt', 'qry', t('ask_model'))

def test(inp):
    return Div(Div(id='msgs'),
    Form(hx_post=ask_llm, hx_target='#msgs', hx_swap='beforeend', cls='flex items-center space-x-2')(inp, Button('提交', type='submit')))
def ex(code, sh):
    res = sh.run_cell(code)
    return res.result if res.result else res.stdout
@rt
def ex_code(code:str, session):
    c,sh = get_chat(session)
    add_hist(c.hist, 'code', f'[INTERPRETER INPUT]\n```py\n{code}\n```')
    res = ex(code, sh)
    add_hist(c.hist, 'code', f'[INTERPRETER OUTPUT]\n```py\n{res}\n```', role='assistant')
    sync_hist(session, c.hist)
    return mk_reply(inp=f'```py\n{code}\n```', out= f'```py\n{res}\n```', color='code', name='code', placeholder=t('your_code'))
@rt
def add_note(note:str, session):
    c,sh = get_chat(session)
    add_hist(c.hist, 'note', content=note,)
    sync_hist(session, c.hist)
    return mk_reply(note, '', 'note', 'note', t('any_thoughts'))
@rt
def code_editor(session): return Form(hx_post=ex_code, hx_target='#msgs', hx_swap='beforeend', cls='flex items-stretch space-x-2')(Inp(placeholder=t('enter_code', session), name='code', onkeydown="if(event.shiftKey && event.key==='Enter') { event.preventDefault(); this.form.requestSubmit(); }"), Button(t('submit', session), type='submit', cls='self-stretch h-auto'))
@rt
def llm_editor(session): return Form(hx_post=ask_llm, hx_target='#msgs', hx_swap='beforeend', cls='flex items-center space-x-2')(Inp(placeholder=t('ask_model', session), name='qry', onkeydown="if(event.shiftKey && event.key==='Enter') { event.preventDefault(); this.form.requestSubmit(); }"), Button(t('submit', session), type='submit', cls='self-stretch h-auto'))
@rt
def note_editor(session): return Form(hx_post=add_note, hx_target='#msgs', hx_swap='beforeend', cls='flex items-center space-x-2')(Inp(placeholder=t('any_thoughts', session), name='note', onkeydown="if(event.shiftKey && event.key==='Enter') { event.preventDefault(); this.form.requestSubmit(); }"), Button(t('submit', session), type='submit', cls='self-stretch h-auto'))
def Tab(title, id, hx_post, **kwargs): return fc.Button(title, id=f'{id}-tab', type='button', role='tab', hx_post=hx_post, hx_target='#editor', hx_swap='innerHTML', **kwargs)
def TabBar(cls='', *args, **kwargs): 
    return Nav(
        Tab(t('code'), id='code', hx_post=code_editor),
        Tab(t('prompt'), id='qry', hx_post=llm_editor),
        Tab(t('note'), id='note', hx_post=note_editor),
        cls=f'w-full {cls}', role='tablist', *args, **kwargs
    )
@rt
def load_messages(session):
    c,sh = get_chat(session)
    for i in c.hist:
        role = i.get('role') if isinstance(i, dict) else i.role
        if role=='user':      yield Div(Bubble(i['content'].replace('[INTERPRETER INPUT]\n', ''), i['type']), cls='space-y-0.5')
        if role=='assistant': yield Div(Bubble(i['content'].replace('[INTERPRETER OUTPUT]\n', ''), i['type'], 'r'), cls='space-y-0.5')
@rt
def edit_dname(session):
    dname = dialogs[(session['userid'], session['current_dialog'])].name
    return Form(id='dname', hx_post=save_dname, hx_target='#dname', hx_swap='outerHTML')(
        Input(value=dname, name='newname', autofocus=True, onfocus='this.select()', required=True, cls='text-2xl font-bold outline-none'),
        Button(t('save', session), type='submit')
    )
@rt 
def save_dname(session, newname:str):
    dialogs.update(uid=session['userid'], dialog_num=session['current_dialog'], name=newname)
    return DialogTitle(newname)
def DialogTitle(name): return H1(name, cls='text-2xl font-bold', id='dname', hx_get=edit_dname, hx_target='#dname', hx_swap='outerHTML')
@rt
def dialog(dnum:int, session): 
    session['current_dialog'] = dnum
    return Div(
        DialogTitle(dialogs[(session['userid'], dnum)].name),
        Div(id='msgs', cls='p-8 max-h-96 overflow-y-auto', hx_get=load_messages, hx_trigger='load'),
        TabBar(id='tabbar'),
        Div(id='editor'),
        cls='tabs w-full'
    )
@rt
def delete_dialog(session, dnum:int):
    uid = session.get('userid')
    dialogs.delete((uid, dnum))
    del user_chats[(uid, dnum)]
insolveit = 'IN_SOLVEIT' in os.environ
@rt
def restore_session(restore_code:str, session):
    if (u:=first(users('restore_code=?', [restore_code]))):
        session['userid'] = u.id
        existing = dialogs(where=f'uid={u.id}')
        if existing: session['current_dialog'] = existing[0].dialog_num
        setsession(session)
        return HtmxResponseHeaders(redirect='/main' if insolveit else '/')
    else: return Div(cls='alert-destructive')(H2(t('restore_failed')), Section(t('restore_error')))

    session['userid'] = first(users('restore_code=?', [restore_code])).id
    setsession(session)
def RestoreForm(session, id='restore-form', *args, **kwargs):
    return Form(hx_post=restore_session, hx_target='#alert-box', cls='flex items-end gap-2', id=id, *args, **kwargs)(
        Div(
            Label(t('restore_code'), ' · ', users[session['userid']].restore_code, fr='restore_code', cls='mb-2'),
            Input(type='text', name='restore_code', placeholder=t('enter_restore_code'))
        ),
        Button(t('submit'), type='submit')
    )
@rt
def current_dialog(session): return dialog(session.get('current_dialog'), session)
def DialogCard(d): return Div(id=f'dialog-{d.uid}{d.dialog_num}', cls='card p-4 hover:bg-gray-100 flex flex-row justify-between items-center')(
    Span(hx_get=dialog.to(dnum=d.dialog_num), hx_target='#content', cls='cursor-pointer')('💬 ', d.name), 
    Button(t('delete'), var='destructive', hx_post=delete_dialog.to(dnum=d.dialog_num), hx_swap='delete', hx_target=f'#dialog-{d.uid}{d.dialog_num}')
)
@rt
def display_dialogs(session):
    ds = L(dialogs('uid=?', [session.get('userid')]))
    ds = ds.map(lambda d: DialogCard(d))
    return Div(cls='flex flex-col gap-2 max-w-xl')(
        Div(cls='flex items-center justify-between gap-4')(H1(t('all_dialogs', session), cls='text-2xl font-bold', id='all-dialogs-title'), RestoreForm(session)), 
        Div(id='alert-box'),
        Div('➕', Span(t('new_dialog', session), id='new-dialog-text'), cls='card p-4 hover:bg-gray-100 cursor-pointer border-2 border-dashed flex flex-row items-center gap-2', hx_post=create_dialog, hx_target='#content'),
        Div(*ds, cls='flex flex-col gap-2 max-h-64 overflow-y-auto')
    )
@rt
def toggle_lang(session):
    lang = 'zh' if session.get('lang') == 'en' else 'en'
    current_lang.set(lang)
    session['lang'] = lang
    return (
        H2(t('solveit_lite'), id='title', hx_swap_oob='true'),
        Button(t('all_dialogs'), id='dialogs-btn', hx_post=display_dialogs, hx_target='#content', var='secondary', hx_swap_oob='true'),
        Span(t('code'), hx_swap_oob='innerHTML:#code-tab'),
        Span(t('prompt'), hx_swap_oob='innerHTML:#qry-tab'),
        Span(t('note'), hx_swap_oob='innerHTML:#note-tab'),
        Div(id='editor', hx_swap_oob='true'),
        Footer(t('footer'), id='footer', cls='text-sm text-gray-400', hx_swap_oob='true'),
        RestoreForm(session, hx_swap_oob='true', id='restore-form'),
        H1(t('all_dialogs'), cls='text-2xl font-bold', id='all-dialogs-title', hx_swap_oob='true'),
        Span(t('new_dialog'), id='new-dialog-text', hx_swap_oob='true')
    )
@rt('/main' if insolveit else '/')
def main(session):
    setsession(session)
    return Div(id='body', cls='card p-8 max-w-4xl mx-auto my-4')(
        Header(cls='flex justify-between items-center')(H2(
            t('solveit_lite'), id='title'), 
            Span(
                Button('🌐', var='secondary', hx_post=toggle_lang, hx_swap='none'), 
                Button(t('all_dialogs'), id='dialogs-btn', hx_post=display_dialogs, hx_target='#content', var='secondary')
            )
        ),
        Section(id='content')(
            current_dialog(session)
        ),
        Footer(t('footer'), id='footer', cls='text-sm text-gray-400')
    )
if not insolveit: serve()
