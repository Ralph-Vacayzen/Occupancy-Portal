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
    units        = sets[sets.PARTNER == partner]['UNIT CODE'].unique()

    isAbleToSubmit   = False
    if len(units) > 0: isAbleToSubmit = True


    st.subheader('Hello, ' + parnter_name + '!')
    st.write('What would you like to do?')
    tab_submit, tab_submitted = st.tabs(['Submit new occupancy','View submitted occupancy'])

    with tab_submit:
        if not isAbleToSubmit:
            target_email = functions.get_target_email_from_partner_situations(partner, sets)

            st.warning('It appears that we do not have any active seasonal beach service units for you.')
            'Please communicate any questions or concerns to: ' + target_email
        
        else:

            tab_manual, tab_upload = st.tabs(['One-by-one','Upload in bulk'])

            with tab_manual:
                l, m, r = st.columns(3)
                list = st.session_state['list']

                unit      = l.selectbox('Unit',units)
                arrival   = m.date_input('Arrival')
                departure = r.date_input('Departure')

                l, r = st.columns(2)

                if l.button('Add to list', use_container_width=True):
                    list.append([unit, arrival, departure])
                
                if r.button('Remove last entry from list', use_container_width=True):
                    list = list[:-1]
                
                st.session_state['list'] = list
                if (len(list) > 0):
                    df = pd.DataFrame(st.session_state['list'], columns=['Unit','Arrival','Departure'])
                    st.dataframe(df,use_container_width=True,hide_index=True)

                    if st.button('Submit', use_container_width=True, type='primary'):
                        print('submit')
                
            
            with tab_upload:
                'placeholder for upload'

    with tab_submitted:

        df = occ[occ.PARTNER == partner]
        df = df[['PROPERTY CODE','ARRIVAL','DEPARTURE']]
        df.columns = ['Unit','Arrival','Departure']

        if (len(df) == 0):
            target_email = functions.get_target_email_from_partner_situations(partner, sets)

            st.warning('It appears that we do not have any occupancy data from you.')
            st.success('If you have submitted occupancy, and you do not see your submission here, it is still under review.')
            'Please communicate any questions or concerns to: ' + target_email

        else:
            st.dataframe(df, hide_index=True, use_container_width=True)