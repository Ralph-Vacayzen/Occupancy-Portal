import streamlit as st
import pandas as pd
import functions

from streamlit_gsheets import GSheetsConnection



conn = st.connection("gsheets", type=GSheetsConnection)
keys = conn.read(worksheet='PARTNERS',  ttl='10m').dropna()
sets = conn.read(worksheet='BEACH',     ttl='10m')
occ  = conn.read(worksheet='OCCUPANCY', ttl='10m')


st.caption('VACAYZEN')
st.title('Occupancy Portal')

st.info('Welcome! This is the place to submit new occupancy or view submitted occupancy to Vacayzen.')


if 'key'           not in st.session_state: st.session_state['key']           = ''
if 'list'          not in st.session_state: st.session_state['list']          = []
if 'button_login'  not in st.session_state: st.session_state['button_login']  = False
if 'button_submit' not in st.session_state: st.session_state['button_submit'] = False

if not st.session_state['button_login']:
    st.session_state['key'] = st.text_input('Please provide your partnernship passkey:')

    if st.button('Login', use_container_width=True):

        if not st.session_state['key'] in keys.PASSKEY.values:
            st.toast('Not a valid passkey.')
            st.session_state['button_login'] = False

        else:
            st.session_state['button_login'] = True
            st.rerun()
    

if st.session_state['button_login']:
    partner      = keys[keys.PASSKEY == st.session_state['key']]['PARTNER'].values[0]
    parnter_name = functions.remove_VRBO_from_partner_name(partner)


    st.subheader('Hello, ' + parnter_name + '!')
    st.write('What would you like to do?')
    tab_submit, tab_submitted = st.tabs(['Submit new occupancy','View submitted occupancy'])


    with tab_submit:

        tab_manual, tab_upload = st.tabs(['One-by-one','Upload in bulk'])

        with tab_manual:
            l, m, r = st.columns(3)
            list = st.session_state['list']

            unit      = l.selectbox('Unit',['Test'])
            arrival   = m.date_input('Arrival')
            departure = r.date_input('Departure')

            if st.button('Add to List', use_container_width=True):
                # df = conn.create(worksheet='TEST',data=occ)
                list.append([unit, arrival, departure])
            
            st.session_state['list'] = list
            df = pd.DataFrame(st.session_state['list'], columns=['Unit','Arrival','Departure'])
            st.dataframe(df,use_container_width=True,hide_index=True)
            
        
        with tab_upload:
            'placeholder for upload'

    with tab_submitted:

        df = occ[occ.PARTNER == partner]
        df = df[['PROPERTY CODE','ARRIVAL','DEPARTURE']]
        df.columns = ['Unit','Arrival','Departure']

        if (len(df) == 0):
            target_email = functions.get_target_email_from_partner_situations(partner, sets)

            'It appears that we do not have any occupancy data from you.'
            'If you have submitted occupancy, and you do not see your submission here, it is still under review.'
            'Please communicate any questions or concerns to: ' + target_email

        else:
            st.dataframe(df, hide_index=True, use_container_width=True)