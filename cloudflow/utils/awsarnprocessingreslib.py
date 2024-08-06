# ========================================
# Import Python Modules (Standard Library)
# ========================================
from dataclasses import dataclass
import re

# =======
# Classes
# =======
@dataclass(frozen=True)
class AWSARNDataCls:
    """
    Data class that stores the parts of an Amazon Resource Name.
    """
    partition: str = ''
    service: str = ''
    region: str = ''
    account_id: str = ''
    resource_id: str = ''

    # === Method ===
    def is_default(self):
        """
        Method that returns True if the instance contains
        only default values, False otherwise.
        """
        return all([getattr(self, elem) == '' for elem in self.__dataclass_fields__])

class AWSARNManagerCls:
    # === Constructor ===
    def __init__(self, arn, arn_parts_num=6):
        """
        Class constructor. Input arguments:
        -) arn: String specifying the Amazon Resurce Name (ARN).
        -) arn_parts_num: Integer specifying the number of parts
        included in the ARN. NOTE: Before changing the default
        value for this input argument, check AWS documentation.
        """
        # Attribute initialization
        self.arn = arn
        self.arn_parts_num = arn_parts_num
        # Sanitize user-provided ARN
        self._sanitize_arn()
        # Validate user-provided ARN
        self._validate_arn()

    # === Protected Method ===
    def _sanitize_arn(self):
        """
        Method that sanitize the user-provided ARN. The main
        objective of the method is to remove from the ARN
        strings (or portions of strings) that cannot be
        processed by the tool.
        NOTE: Some strings have to be removed because their
        processing is not currently supported, but they might
        in future versions of the tool. To be reviewed.
        """
        # Regular expression that identifies the syntax used
        # to specify AWS-specific parameters as shown in this
        # example: #{AWS::Region}. The occurrence of '::' is
        # removed, as this syntax is not currently supported,
        # and it would prevent the validation of the ARN.
        detect_param_reg_exp = re.compile(r'#\{(?P<provider>\w+)::(?P<parameter>\w+)\}')
        self.arn = detect_param_reg_exp.sub(r'\g<provider>\g<parameter>', self.arn)

    # === Protected Method ===
    def _validate_arn(self):
        """
        Method that validates the user-provided ARN, and initializes
        an object storing the various parts of the ARN. If the ARN
        is invalid, the latter object will contain default values. 
        """
        # Validate user-provided ARN by identifying its parts
        try:
            # Initialize instance of the object storing the ARN parts.
            # If an exception is raised during the validation of the
            # ARN, this object will store the default values defined
            # in the relevant data class.
            self.aws_arn_data = AWSARNDataCls()
            # Identify the parts of the ARN by calling string method split
            arn_parts = self.arn.split(':')
            if len(arn_parts) != self.arn_parts_num:
                # Raise an exception if the number of parts detected
                # within the ARN is not the expected one.
                raise ValueError('Inconsistency detected - Number of ARN parts is invalid')
            # The first part of the ARN does not contain useful information,
            # as it is always set to string 'arn'. It is therefore removed.
            arn_parts.pop(0)
            # Initialize the ARN data object with the substrings obtained
            # from the user-provided ARN.
            self.aws_arn_data = AWSARNDataCls(*arn_parts)
        except Exception as e:
            print('--- Invalid ARN detected - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def get_account_id(self):
        """
        Method that returns the ARN account_id as a string.
        """
        return self.aws_arn_data.account_id

    # === Method ===
    def get_partition(self):
        """
        Method that returns the ARN partition as a string. 
        """
        return self.aws_arn_data.partition

    # === Method ===
    def get_region(self):
        """
        Method that returns the ARN region as a string.
        """
        return self.aws_arn_data.region

    # === Method ===
    def get_resource_id(self):
        """
        Method that returns the ARN resource_id as a string.
        """
        return self.aws_arn_data.resource_id

    # === Method ===
    def get_service(self):
        """
        Method that returns the ARN service as a string.
        """
        return self.aws_arn_data.service

    # === Method ===
    def is_valid(self):
        """
        Method that returns True if the string passed to
        the constructor is a valid ARN, False otherwise.
        """
        # An invalid ARN raises an exception that prevents
        # the extraction of the ARN fields. In this case,
        # the instance of the data class AWSARNDataCls
        # contains only default values.
        return not self.aws_arn_data.is_default()
